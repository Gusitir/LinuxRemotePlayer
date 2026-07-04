# Scripts SQL para Supabase (Auditoría)

A continuación te dejo los scripts SQL que debes ejecutar en el **SQL Editor** de tu panel de Supabase. Estos resuelven los problemas de seguridad detectados en la auditoría sin que yo tenga que tocar tu base de datos directamente.

## 1. Rate Limiting Básico (SEC-02)

Para evitar que alguien haga fuerza bruta a tus tags, creamos un rate limit simple por IP (si Supabase lo permite en tu plan) o por bloqueos. Una forma sencilla en Supabase usando Postgres estándar es registrar intentos:

```sql
-- 1. Crear tabla para rastrear intentos de claim
CREATE TABLE IF NOT EXISTS public.claim_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ip_address TEXT,
    user_id UUID,
    attempted_at TIMESTAMPTZ DEFAULT NOW(),
    tag_uid TEXT
);

-- Habilitar RLS en esta tabla para que nadie la lea
ALTER TABLE public.claim_attempts ENABLE ROW LEVEL SECURITY;

-- 2. Modificar la función 'claim_nfc_tag' para incluir el rate limit
-- (Deberás agregar esto AL INICIO de tu función actual claim_nfc_tag)
/*
  DECLARE
    recent_attempts INT;
  BEGIN
    -- Contar intentos del usuario en el último minuto
    SELECT COUNT(*) INTO recent_attempts
    FROM public.claim_attempts
    WHERE user_id = auth.uid() AND attempted_at > NOW() - INTERVAL '1 minute';
    
    IF recent_attempts > 10 THEN
      RAISE EXCEPTION 'Rate limit exceeded. Please wait a minute.';
    END IF;

    -- Registrar este intento
    INSERT INTO public.claim_attempts(user_id, tag_uid) VALUES (auth.uid(), p_tag_uid);
    
    -- ... AQUI CONTINÚA TU LÓGICA NORMAL ...
*/
```

## 2. Bloqueo de Trampas de XP / Anti-Farmeo (SEC-03)

Para evitar que los usuarios editen su propia experiencia o nivel mediante la API de Supabase, debemos asegurarnos de que la tabla `pets` solo permita lectura (SELECT) desde el cliente, y que toda modificación ocurra *únicamente* a través de tus RPC (`interact_pet`).

```sql
-- Asegurar que la tabla pets tiene RLS
ALTER TABLE public.pets ENABLE ROW LEVEL SECURITY;

-- Eliminar cualquier policy antigua de UPDATE si existe
DROP POLICY IF EXISTS "Users can update their own pets" ON public.pets;
DROP POLICY IF EXISTS "Enable update for users based on owner_id" ON public.pets;

-- Asegurar que los usuarios solo puedan VER sus mascotas (o todas si es público)
-- (Si los espectadores anónimos pueden verlas, la política de SELECT debe ser pública)
DROP POLICY IF EXISTS "Enable read access for all users" ON public.pets;
CREATE POLICY "Enable read access for all users" ON public.pets FOR SELECT USING (true);

-- IMPORTANTE: No crees políticas de UPDATE o INSERT para la tabla 'pets'.
-- Las funciones 'SECURITY DEFINER' (como claim_nfc_tag e interact_pet) ignoran 
-- el RLS internamente, por lo que ellas sí podrán actualizar la tabla.
```

## 3. Entropía en los Códigos QR (SEC-02)

A partir de ahora, los códigos generados en tus etiquetas NFC/QR **nunca** deben ser predecibles (como `TAG-001`, `TAG-002`).

Utiliza el formato UUID v4 o cadenas aleatorias de 22 caracteres alfanuméricos cuando generes lotes nuevos en tu sistema físico.
```sql
-- Ejemplo de inserción de un nuevo tag seguro en la DB:
INSERT INTO public.nfc_tags (tag_uid, batch_id) 
VALUES (gen_random_uuid(), 'LOTE_1');
```
