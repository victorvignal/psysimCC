-- Rodar no Supabase Dashboard > SQL Editor
-- https://supabase.com/dashboard/project/hepekrvzmpzzludivhjc/sql/new

ALTER TABLE sessions        ADD COLUMN IF NOT EXISTS user_id uuid REFERENCES auth.users(id);
ALTER TABLE supervisions    ADD COLUMN IF NOT EXISTS user_id uuid REFERENCES auth.users(id);
ALTER TABLE active_sessions ADD COLUMN IF NOT EXISTS user_id uuid REFERENCES auth.users(id);

CREATE INDEX IF NOT EXISTS sessions_user_id_idx       ON sessions(user_id);
CREATE INDEX IF NOT EXISTS supervisions_user_id_idx   ON supervisions(user_id);
CREATE INDEX IF NOT EXISTS active_sessions_user_id_idx ON active_sessions(user_id);

ALTER TABLE sessions        ENABLE ROW LEVEL SECURITY;
ALTER TABLE supervisions    ENABLE ROW LEVEL SECURITY;
ALTER TABLE active_sessions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "service_role_all_sessions"
  ON sessions FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "service_role_all_supervisions"
  ON supervisions FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "service_role_all_active_sessions"
  ON active_sessions FOR ALL TO service_role USING (true) WITH CHECK (true);
