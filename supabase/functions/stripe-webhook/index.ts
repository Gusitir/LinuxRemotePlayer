import { serve } from "https://deno.land/std@0.190.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.39.0'
import Stripe from 'npm:stripe@^12.0.0'

const stripe = new Stripe(Deno.env.get('STRIPE_SECRET_KEY') as string, {
  httpClient: Stripe.createFetchHttpClient(),
});
const cryptoProvider = Stripe.createSubtleCryptoProvider();
const stripeWebhookSecret = Deno.env.get('STRIPE_WEBHOOK_SECRET')!;

function generateLicenseKey(): string {
  const allowed = 'ABCDEFGHJKLMNPQRSTVWXYZ23456789';
  const array = new Uint8Array(12);
  crypto.getRandomValues(array);
  
  let key = 'LRP-';
  for (let i = 0; i < 12; i++) {
    const charIndex = array[i] % allowed.length;
    key += allowed.charAt(charIndex);
    if (i === 3 || i === 7) {
      key += '-';
    }
  }
  return key;
}

serve(async (req) => {
  if (req.method !== 'POST') {
    return new Response('Method Not Allowed', { status: 405 })
  }

  const signature = req.headers.get('Stripe-Signature');
  if (!signature) {
    return new Response('Missing Stripe-Signature header', { status: 400 })
  }

  const body = await req.text();

  let event;
  try {
    event = await stripe.webhooks.constructEventAsync(
      body,
      signature,
      stripeWebhookSecret,
      undefined,
      cryptoProvider
    );
  } catch (err) {
    console.error('Webhook signature verification failed:', err.message);
    return new Response(`Webhook Error: ${err.message}`, { status: 400 })
  }

  if (event.type === 'checkout.session.completed') {
    const session = event.data.object;
    const email = session.customer_details?.email;
    const customerId = session.customer;
    const sessionId = session.id;

    if (!email) {
      console.error('Session has no customer details email');
      return new Response('Missing customer email', { status: 400 })
    }

    try {
      const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
      const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
      const supabase = createClient(supabaseUrl, supabaseServiceKey);

      // Check if session already processed (Idempotency - C1-2a)
      const { data: existingLicense, error: queryErr } = await supabase
        .from('licenses')
        .select('token')
        .eq('stripe_session_id', sessionId)
        .maybeSingle();

      if (queryErr) {
        console.error('Query existing license error:', queryErr);
      }

      if (existingLicense) {
        console.log(`License for stripe session ${sessionId} already created: ${existingLicense.token}`);
        return new Response(JSON.stringify({ received: true, status: 'existing' }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      }

      // Generate key & Insert to DB
      const key = generateLicenseKey();
      const { error: insertErr } = await supabase
        .from('licenses')
        .insert({
          token: key,
          email: email,
          plan: 'lifetime',
          stripe_customer_id: customerId,
          stripe_session_id: sessionId,
          active: true
        });

      if (insertErr) {
        console.error('Failed to insert license into database:', insertErr);
        return new Response('Database error', { status: 500 })
      }

      console.log(`Generated new license key: ${key} for email: ${email}`);

      // Send license email via Resend API
      const resendApiKey = Deno.env.get('RESEND_API_KEY');
      if (resendApiKey) {
        const fromEmail = Deno.env.get('RESEND_FROM') || 'onboarding@resend.dev';
        const buyUrl = Deno.env.get('BUY_URL') || 'https://linux-remote-player.vercel.app';

        try {
          const resendResponse = await fetch('https://api.resend.com/emails', {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${resendApiKey}`,
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              from: `LinuxRemotePlayer <${fromEmail}>`,
              to: email,
              subject: 'Tu licencia de LinuxRemotePlayer',
              html: `
                <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e5e7eb; border-radius: 8px;">
                  <h2 style="color: #3b82f6; margin-top: 0;">¡Gracias por tu compra!</h2>
                  <p>Aquí tienes tu clave de licencia para desbloquear el control por voz con IA en tu LinuxRemotePlayer:</p>
                  <div style="background-color: #f3f4f6; padding: 15px; border-radius: 6px; font-family: monospace; font-size: 18px; font-weight: bold; text-align: center; margin: 20px 0; letter-spacing: 2px;">
                    ${key}
                  </div>
                  <h3 style="color: #111827;">Pasos para activarla:</h3>
                  <ol style="line-height: 1.6; padding-left: 20px;">
                    <li>Abre la aplicación <strong>Remote Kiosk</strong> en tu teléfono.</li>
                    <li>Entra en <strong>Ajustes</strong> (icono de engranaje) y ve a la sección <strong>Clave de licencia</strong>.</li>
                    <li>Pega la clave de arriba y toca <strong>Activar</strong>.</li>
                  </ol>
                  <p style="margin-top: 20px; font-size: 14px; color: #6b7280;">
                    También puedes activar la licencia abriendo este enlace desde el navegador del teléfono en tu red local:
                    <br>
                    <a href="https://TU-TV.local:8000/?license=${key}" style="color: #3b82f6; text-decoration: underline;">
                      https://TU-TV.local:8000/?license=${key}
                    </a>
                  </p>
                  <hr style="border: 0; border-top: 1px solid #e5e7eb; margin: 20px 0;">
                  <p style="font-size: 12px; color: #9ca3af; text-align: center; margin-bottom: 0;">
                    ¿Tienes problemas? Escríbenos a <a href="mailto:aeciminer02@gmail.com" style="color: #3b82f6;">aeciminer02@gmail.com</a>
                  </p>
                </div>
              `,
            }),
          });

          if (!resendResponse.ok) {
            const errBody = await resendResponse.text();
            console.error('Resend API call failed:', errBody);
          } else {
            console.log('License email successfully sent to', email);
          }
        } catch (emailErr) {
          console.error('Error occurred sending Resend email:', emailErr);
        }
      } else {
        console.warn('RESEND_API_KEY is not configured. Email was not sent.');
      }

    } catch (dbErr) {
      console.error('Database connection/insertion error:', dbErr);
      return new Response('Server Error', { status: 500 })
    }
  }

  return new Response(JSON.stringify({ received: true }), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
  })
})
