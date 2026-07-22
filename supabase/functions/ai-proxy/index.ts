// ai-proxy — voice pipeline server-side (v1.9).
// The HTPC backend sends {token, device_id, targets, audio}; this function enforces
// kill-switch, global cap, license, device activation and per-plan quota atomically
// (consume_voice RPC), then calls Together AI (STT + intent LLM). Together keys live
// ONLY in Supabase secrets. Server-to-server: no CORS needed.
import { serve } from "https://deno.land/std@0.190.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.39.0'

const TOGETHER_KEY = Deno.env.get('TOGETHER_API_KEY') ?? '';
const STT_URL = Deno.env.get('TOGETHER_STT_URL') ?? 'https://api.together.xyz/v1/audio/transcriptions';
const STT_MODEL = Deno.env.get('TOGETHER_STT_MODEL') ?? 'openai/whisper-large-v3';
const LLM_URL = Deno.env.get('TOGETHER_LLM_URL') ?? 'https://api.together.xyz/v1/chat/completions';
const LLM_MODEL = Deno.env.get('TOGETHER_LLM_MODEL') ?? 'Qwen/Qwen2.5-7B-Instruct-Turbo';

const MAX_AUDIO_BYTES = 512_000; // ~60s Opus; hard server-side cap (anti-abuse)
const ALLOWED_ACTIONS = new Set(['launch_kiosk', 'media_control', 'search']);

// In-memory rate limiting map (10 req/min per token) — same scheme as validate-license
const rateLimitMap = new Map<string, { count: number; resetAt: number }>();

function checkRateLimit(token: string): boolean {
  const now = Date.now();
  const entry = rateLimitMap.get(token);
  if (!entry || now > entry.resetAt) {
    rateLimitMap.set(token, { count: 1, resetAt: now + 60000 });
    return true;
  }
  if (entry.count >= 10) {
    return false;
  }
  entry.count++;
  return true;
}

function json(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

// Strip markdown fences and extract the first {...} block (port of ai_pipeline.py)
function cleanJsonContent(content: string): string {
  content = content.trim().replace(/^```(?:json)?\s*/, '').replace(/\s*```$/, '');
  const m = content.match(/\{[\s\S]*\}/);
  return m ? m[0] : content;
}

function buildSystemPrompt(targets: string[]): string {
  const validAppsStr = targets.join(', ');
  return `
You are an intent parser for a TV remote. Output ONLY valid JSON.
Allowed actions: 'launch_kiosk', 'media_control', 'search'.

Valid app targets (launch_kiosk): [${validAppsStr}]
Valid media keys (media_control): KEY_VOLUMEUP, KEY_VOLUMEDOWN, KEY_MUTE, KEY_PLAYPAUSE, KEY_PLAY, KEY_PAUSE, KEY_STOP, KEY_NEXTSONG, KEY_PREVIOUSSONG, KEY_FASTFORWARD, KEY_REWIND

NOTE: The user speaks Spanish. Map synonyms accordingly (e.g., sube/baja volumen, pausa, silencio, adelanta...).

Examples:
1. "abre netflix" -> {"action": "launch_kiosk", "parameters": {"target_id": "netflix"}}
2. "pon youtube de gatitos" -> {"action": "launch_kiosk", "parameters": {"target_id": "youtube", "search_query": "gatitos"}}
3. "sube el volumen" -> {"action": "media_control", "parameters": {"key": "KEY_VOLUMEUP"}}
4. "pausa el video" -> {"action": "media_control", "parameters": {"key": "KEY_PLAYPAUSE"}}
5. "silencio" -> {"action": "media_control", "parameters": {"key": "KEY_MUTE"}}
6. "busca recetas de cocina" -> {"action": "search", "parameters": {"search_query": "recetas de cocina"}}
`;
}

serve(async (req) => {
  if (req.method !== 'POST') {
    return json(405, { error: 'POST only' });
  }

  try {
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
    const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
    const supabase = createClient(supabaseUrl, supabaseServiceKey);

    const ct = req.headers.get('content-type') ?? '';

    // ---- JSON branch: license activation / release ----
    if (ct.includes('application/json')) {
      const body = await req.json();
      const token = body.token;
      const deviceId = body.device_id;
      if (!token || typeof token !== 'string' || !deviceId || typeof deviceId !== 'string') {
        return json(400, { error: 'Missing token/device_id' });
      }
      if (!checkRateLimit(token)) {
        return json(429, { error: 'Too many requests' });
      }

      if (body.action === 'activate') {
        const { data, error } = await supabase.rpc('claim_device', {
          p_token: token, p_device_id: deviceId, p_force: !!body.force,
        });
        if (error || !data) {
          console.error('claim_device RPC error:', error);
          return json(500, { error: 'claim failed' });
        }
        const status = data.status === 'activated' ? 200
          : data.status === 'in_use_elsewhere' ? 409 : 403;
        return json(status, data);
      }

      if (body.action === 'release') {
        const { data, error } = await supabase.rpc('release_device', {
          p_token: token, p_device_id: deviceId,
        });
        if (error) {
          console.error('release_device RPC error:', error);
          return json(500, { error: 'release failed' });
        }
        return json(200, { released: !!data });
      }

      return json(400, { error: 'Unknown action' });
    }

    // ---- multipart branch: voice command ----
    if (!ct.includes('multipart/form-data')) {
      return json(415, { error: 'Expected multipart/form-data or application/json' });
    }

    const form = await req.formData();
    const token = form.get('token');
    const deviceId = form.get('device_id');
    const targetsRaw = form.get('targets');
    const audio = form.get('audio');

    if (typeof token !== 'string' || !token
      || typeof deviceId !== 'string' || !deviceId
      || !(audio instanceof File)) {
      return json(400, { error: 'Missing token/device_id/audio' });
    }
    if (!checkRateLimit(token)) {
      return json(429, { error: 'Too many requests' });
    }
    // Size cap BEFORE consuming quota: an oversized blob must not burn a command.
    if (audio.size > MAX_AUDIO_BYTES) {
      return json(413, { ok: false, reason: 'audio_too_large' });
    }

    let targets: string[] = [];
    if (typeof targetsRaw === 'string' && targetsRaw) {
      try {
        const parsed = JSON.parse(targetsRaw);
        if (Array.isArray(parsed)) {
          targets = parsed.filter((t) => typeof t === 'string').slice(0, 100);
        }
      } catch (_) { /* malformed targets -> empty list */ }
    }

    // Atomic gate: kill-switch, global cap, license, device activation, per-plan quota
    const { data: gate, error: gateErr } = await supabase.rpc('consume_voice', {
      p_token: token, p_device_id: deviceId, p_audio_bytes: audio.size,
    });
    if (gateErr || !gate) {
      console.error('consume_voice RPC error:', gateErr);
      return json(500, { error: 'gate failed' });
    }
    if (!gate.ok) {
      const statusByReason: Record<string, number> = {
        service_disabled: 503,
        global_cap: 503,
        invalid_license: 403,
        in_use_elsewhere: 409,
        quota_exceeded: 429,
      };
      return json(statusByReason[gate.reason] ?? 403, gate);
    }

    if (!TOGETHER_KEY) {
      console.error('TOGETHER_API_KEY secret is missing');
      return json(503, { ok: false, reason: 'service_misconfigured' });
    }

    // STT (Together Whisper)
    const sttForm = new FormData();
    sttForm.append('model', STT_MODEL);
    sttForm.append('file', audio, audio.name || 'audio.webm');
    const sttRes = await fetch(STT_URL, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${TOGETHER_KEY}` },
      body: sttForm,
    });
    if (!sttRes.ok) {
      console.error('STT error:', sttRes.status, await sttRes.text());
      return json(502, { ok: false, reason: 'stt_error' });
    }
    const text = (((await sttRes.json()).text ?? '') as string).trim();
    if (!text) {
      return json(200, { ok: false, reason: 'no_speech', remaining_today: gate.remaining_today });
    }

    // Intent (Together LLM)
    const llmRes = await fetch(LLM_URL, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${TOGETHER_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: LLM_MODEL,
        messages: [
          { role: 'system', content: buildSystemPrompt(targets) },
          { role: 'user', content: text },
        ],
        response_format: { type: 'json_object' },
      }),
    });
    if (!llmRes.ok) {
      console.error('LLM error:', llmRes.status, await llmRes.text());
      return json(502, { ok: false, reason: 'llm_error', text });
    }
    const content = (await llmRes.json()).choices?.[0]?.message?.content ?? '';
    let intent: { action?: string } = { action: 'error' };
    try {
      intent = JSON.parse(cleanJsonContent(content));
    } catch (_) {
      intent = { action: 'error' };
    }
    if (!ALLOWED_ACTIONS.has(intent.action ?? '')) {
      intent = { action: 'error' };
    }

    return json(200, { ok: true, text, intent, remaining_today: gate.remaining_today });

  } catch (err) {
    console.error('ai-proxy unexpected error:', err);
    return json(500, { error: 'internal' });
  }
})
