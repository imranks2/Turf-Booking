import { useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { useAuth } from '@/hooks/useAuth';
import { loginSchema, registerSchema } from '@/utils/validators';

type Mode = 'login' | 'register';

export function Login(): JSX.Element {
  const { login, register } = useAuth();
  const navigate = useNavigate();
  const [mode, setMode] = useState<Mode>('login');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    const form = new FormData(event.currentTarget);
    const raw = Object.fromEntries(form.entries());
    try {
      if (mode === 'login') {
        const parsed = loginSchema.parse(raw);
        await login(parsed);
        navigate('/');
      } else {
        const parsed = registerSchema.parse({ ...raw, role: 'player' });
        await register(parsed);
        await login({ email: parsed.email, password: parsed.password });
        navigate('/');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="mx-auto max-w-md px-4 py-12">
      <Card>
        <h1 className="mb-1 text-xl font-bold text-gray-900">
          {mode === 'login' ? 'Welcome back' : 'Create your account'}
        </h1>
        <p className="mb-6 text-sm text-gray-500">
          {mode === 'login' ? 'Sign in to book turfs.' : 'Sign up as a player to start booking.'}
        </p>
        <form className="space-y-4" onSubmit={(e) => void handleSubmit(e)}>
          {mode === 'register' && (
            <>
              <Input id="name" name="name" label="Full name" required />
              <Input id="phone" name="phone" label="Phone" placeholder="+91..." required />
            </>
          )}
          <Input id="email" name="email" type="email" label="Email" required />
          <Input id="password" name="password" type="password" label="Password" required />
          {error && <p className="text-sm text-red-500">{error}</p>}
          <Button type="submit" className="w-full" loading={submitting}>
            {mode === 'login' ? 'Sign in' : 'Create account'}
          </Button>
        </form>
        <button
          type="button"
          className="mt-4 w-full text-center text-sm text-brand-600 hover:text-brand-700"
          onClick={() => {
            setError(null);
            setMode((m) => (m === 'login' ? 'register' : 'login'));
          }}
        >
          {mode === 'login' ? 'New here? Create an account' : 'Already have an account? Sign in'}
        </button>
      </Card>
    </div>
  );
}
