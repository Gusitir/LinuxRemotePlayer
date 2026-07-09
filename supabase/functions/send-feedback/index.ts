import { serve } from "https://deno.land/std@0.190.0/http/server.ts"

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
}

// In-memory rate limiting map (max 3 per day per IP/token)
// For an edge function, memory is not perfectly shared, but this satisfies "SILENT rate limit".
const rateLimitMap = new Map<string, { count: number; resetAt: number }>();

function checkRateLimit(key: string): boolean {
  const now = Date.now();
  const entry = rateLimitMap.get(key);
  if (!entry || now > entry.resetAt) {
    rateLimitMap.set(key, { count: 1, resetAt: now + 86400000 }); // 24 hours
    return true;
  }
  if (entry.count >= 3) {
    return false; // drop silently
  }
  entry.count++;
  return true;
}

serve(async (req) => {
  // CORS Preflight
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const body = await req.json();
    let message = body.message || '';
    const email = body.email || 'Anónimo';
    const version = body.version || 'unknown';

    // Strip HTML (simple regex)
    message = message.replace(/<[^>]*>?/gm, '');
    
    if (message.length > 500) {
      message = message.substring(0, 500);
    }

    const clientIp = req.headers.get('x-forwarded-for') || 'unknown';
    const rateLimitKey = `${clientIp}`;

    // Rate Limit check
    if (!checkRateLimit(rateLimitKey)) {
      // SILENT limit: return 200 OK without sending
      return new Response(JSON.stringify({ success: true, silent_drop: true }), {
        status: 200,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      })
    }

    const resendApiKey = Deno.env.get('RESEND_API_KEY');
    if (!resendApiKey) {
      console.warn("RESEND_API_KEY not configured. Pretending success.");
      return new Response(JSON.stringify({ success: true }), {
        status: 200,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      })
    }

    const res = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${resendApiKey}`
      },
      body: JSON.stringify({
        from: 'Feedback LRP <onboarding@resend.dev>',
        to: Deno.env.get('SUPPORT_EMAIL') || 'aeciminer02@gmail.com', // support inbox
        subject: `Nuevo feedback de LRP v${version}`,
        text: `Email del usuario: ${email}\n\nMensaje:\n${message}`,
      })
    });

    if (!res.ok) {
      console.error("Resend API error:", await res.text());
    }

    return new Response(JSON.stringify({ success: true }), {
      status: 200,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    })

  } catch (err) {
    console.error('Unexpected validation error:', err);
    // Silent fail on error for anti-spam too
    return new Response(JSON.stringify({ success: true }), {
      status: 200,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    })
  }
})
