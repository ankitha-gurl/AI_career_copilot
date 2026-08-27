import { useEffect, useState } from 'react';
import axios from 'axios';
import { ArrowRight, Briefcase, CheckCircle2, Sparkles, Target, TrendingUp, UserCircle, ShieldCheck } from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
});

const featureCards = [
  {
    icon: Briefcase,
    title: 'Career roadmap',
    text: 'Turn your profile into a practical move-by-move professional plan.',
  },
  {
    icon: Target,
    title: 'Job-fit analysis',
    text: 'Identify the most relevant job roles for your skills and experience.',
  },
  {
    icon: TrendingUp,
    title: 'Interview readiness',
    text: 'Prepare for technical and behavioral interviews with a focused plan.',
  },
];

const roadmap = [
  'Polish your resume for the roles you want next.',
  'Build 2 projects that match your target job descriptions.',
  'Practice mock interviews and improve weak areas weekly.',
  'Apply consistently and track real-world outcomes.',
];

const defaultForm = {
  full_name: '',
  email: '',
  password: '',
};

function App() {
  const [mode, setMode] = useState('login');
  const [form, setForm] = useState(defaultForm);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const token = localStorage.getItem('ai_career_token');

    if (!token) {
      return;
    }

    api
      .get('/users/me', {
        headers: { Authorization: `Bearer ${token}` },
      })
      .then((response) => setUser(response.data))
      .catch(() => {
        localStorage.removeItem('ai_career_token');
      });
  }, []);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError('');

    try {
      const endpoint = mode === 'login' ? '/auth/login' : '/auth/register';
      const payload = mode === 'login'
        ? { email: form.email, password: form.password }
        : { full_name: form.full_name, email: form.email, password: form.password };

      const response = await api.post(endpoint, payload);

      if (mode === 'login') {
        const token = response.data.access_token;
        localStorage.setItem('ai_career_token', token);
        setUser(response.data.user);
        setForm(defaultForm);
      } else {
        setMode('login');
        setForm(defaultForm);
      }
    } catch (requestError) {
      const message = requestError.response?.data?.detail || 'Something went wrong. Please try again.';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('ai_career_token');
    setUser(null);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      <div className="mx-auto max-w-7xl px-6 py-8">
        <header className="mb-16 flex items-center justify-between rounded-full border border-slate-800 bg-slate-900/80 px-5 py-3 backdrop-blur">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-500/20 text-xl text-blue-300">✦</div>
            <div>
              <p className="text-xs uppercase tracking-[0.25em] text-slate-400">Portfolio</p>
              <h2 className="text-lg font-semibold">AI Career Copilot</h2>
            </div>
          </div>

          <button
            type="button"
            onClick={() => setMode('login')}
            className="rounded-full border border-slate-700 px-4 py-2 text-sm font-medium text-slate-200 hover:border-slate-500"
          >
            {user ? 'Dashboard' : 'Login'}
          </button>
        </header>

        {!user ? (
          <main className="grid gap-10 lg:grid-cols-[1.2fr_0.8fr] lg:items-center">
            <section>
              <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-blue-500/30 bg-blue-500/10 px-3 py-1 text-sm font-medium text-blue-200">
                <Sparkles size={16} />
                Career clarity with AI support
              </div>

              <h1 className="max-w-xl text-5xl font-black tracking-tight text-white md:text-6xl">
                Build a career plan that actually moves you forward.
              </h1>

              <p className="mt-6 max-w-xl text-lg text-slate-300">
                AI Career Copilot helps you identify the best opportunities, strengthen weak areas, and stay consistent with a focused roadmap.
              </p>

              <div className="mt-8 flex flex-wrap gap-4">
                <button
                  type="button"
                  onClick={() => setMode('register')}
                  className="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-6 py-3 font-semibold text-white shadow-lg shadow-blue-900/50 transition hover:bg-blue-500"
                >
                  Get started <ArrowRight size={18} />
                </button>
                <button
                  type="button"
                  onClick={() => setMode('login')}
                  className="rounded-xl border border-slate-700 px-6 py-3 font-semibold text-slate-200 transition hover:border-slate-500"
                >
                  I already have an account
                </button>
              </div>

              <div className="mt-12 grid gap-4 md:grid-cols-3">
                {featureCards.map(({ icon: Icon, title, text }) => (
                  <div key={title} className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
                    <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-xl bg-blue-500/10 text-blue-300">
                      <Icon size={20} />
                    </div>
                    <h3 className="mb-2 text-lg font-semibold text-white">{title}</h3>
                    <p className="text-sm leading-6 text-slate-400">{text}</p>
                  </div>
                ))}
              </div>
            </section>

            <aside className="rounded-3xl border border-slate-800 bg-slate-900 p-6 shadow-2xl shadow-slate-950/40">
              <div className="mb-6 flex items-center justify-between">
                <div>
                  <p className="text-sm uppercase tracking-[0.2em] text-slate-400">{mode === 'login' ? 'Welcome back' : 'Create account'}</p>
                  <h3 className="mt-2 text-2xl font-bold text-white">{mode === 'login' ? 'Sign in' : 'Register'}</h3>
                </div>
                <div className="rounded-full bg-emerald-500/15 p-2 text-emerald-300">
                  <ShieldCheck size={20} />
                </div>
              </div>

              <form className="space-y-4" onSubmit={handleSubmit}>
                {mode === 'register' && (
                  <label className="block">
                    <span className="mb-2 block text-sm text-slate-300">Full name</span>
                    <input
                      type="text"
                      name="full_name"
                      value={form.full_name}
                      onChange={handleChange}
                      className="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none ring-0 transition placeholder:text-slate-500 focus:border-blue-500"
                      placeholder="Jane Doe"
                      required
                    />
                  </label>
                )}

                <label className="block">
                  <span className="mb-2 block text-sm text-slate-300">Email</span>
                  <input
                    type="email"
                    name="email"
                    value={form.email}
                    onChange={handleChange}
                    className="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none transition placeholder:text-slate-500 focus:border-blue-500"
                    placeholder="you@example.com"
                    required
                  />
                </label>

                <label className="block">
                  <span className="mb-2 block text-sm text-slate-300">Password</span>
                  <input
                    type="password"
                    name="password"
                    value={form.password}
                    onChange={handleChange}
                    className="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none transition placeholder:text-slate-500 focus:border-blue-500"
                    placeholder="••••••••"
                    required
                  />
                </label>

                {error && (
                  <div className="rounded-xl border border-red-500/40 bg-red-500/10 px-3 py-2 text-sm text-red-200">
                    {error}
                  </div>
                )}

                <button
                  type="submit"
                  disabled={loading}
                  className="mt-2 w-full rounded-xl bg-blue-600 px-4 py-3 font-semibold text-white transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-70"
                >
                  {loading ? 'Please wait...' : mode === 'login' ? 'Login' : 'Create account'}
                </button>
              </form>

              <div className="mt-6 text-center text-sm text-slate-400">
                {mode === 'login' ? 'Need an account?' : 'Already registered?'}{' '}
                <button
                  type="button"
                  onClick={() => setMode(mode === 'login' ? 'register' : 'login')}
                  className="font-medium text-blue-300 hover:text-blue-200"
                >
                  {mode === 'login' ? 'Sign up' : 'Sign in'}
                </button>
              </div>
            </aside>
          </main>
        ) : (
          <main className="space-y-8">
            <div className="rounded-3xl border border-slate-800 bg-slate-900 p-6 md:flex md:items-center md:justify-between">
              <div className="flex items-center gap-4">
                <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-500/15 text-blue-200">
                  <UserCircle size={28} />
                </div>
                <div>
                  <p className="text-sm uppercase tracking-[0.2em] text-slate-400">Profile</p>
                  <h2 className="mt-2 text-2xl font-bold text-white">{user.full_name}</h2>
                  <p className="text-slate-300">{user.email}</p>
                </div>
              </div>

              <button
                type="button"
                onClick={logout}
                className="mt-5 rounded-xl border border-slate-700 px-4 py-2 text-sm font-medium text-slate-200 hover:border-slate-500 md:mt-0"
              >
                Log out
              </button>
            </div>

            <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
              <section className="rounded-3xl border border-slate-800 bg-slate-900 p-6">
                <div className="mb-6 flex items-center gap-3">
                  <div className="rounded-xl bg-violet-500/15 p-2 text-violet-200">
                    <CheckCircle2 size={20} />
                  </div>
                  <div>
                    <p className="text-sm uppercase tracking-[0.25em] text-slate-400">Career momentum</p>
                    <h3 className="text-xl font-bold text-white">Your next move</h3>
                  </div>
                </div>

                <div className="space-y-4">
                  {roadmap.map((step, index) => (
                    <div key={step} className="flex items-start gap-3 rounded-2xl border border-slate-800 bg-slate-950/60 p-4">
                      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-500/15 text-sm font-bold text-blue-200">
                        {index + 1}
                      </div>
                      <p className="pt-1 text-slate-200">{step}</p>
                    </div>
                  ))}
                </div>
              </section>

              <aside className="rounded-3xl border border-slate-800 bg-slate-900 p-6">
                <p className="text-sm uppercase tracking-[0.25em] text-slate-400">Progress snapshot</p>
                <div className="mt-6 space-y-5">
                  <div>
                    <p className="text-slate-400">Resume completion</p>
                    <div className="mt-2 h-2.5 rounded-full bg-slate-800">
                      <div className="h-2.5 w-[82%] rounded-full bg-emerald-400" />
                    </div>
                  </div>

                  <div>
                    <p className="text-slate-400">Interview readiness</p>
                    <div className="mt-2 h-2.5 rounded-full bg-slate-800">
                      <div className="h-2.5 w-[68%] rounded-full bg-blue-400" />
                    </div>
                  </div>

                  <div>
                    <p className="text-slate-400">Portfolio strength</p>
                    <div className="mt-2 h-2.5 rounded-full bg-slate-800">
                      <div className="h-2.5 w-[75%] rounded-full bg-violet-400" />
                    </div>
                  </div>
                </div>
              </aside>
            </div>
          </main>
        )}
      </div>
    </div>
  );
}

export default App;