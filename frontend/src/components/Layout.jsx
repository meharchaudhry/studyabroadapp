import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom';
import {
  Home, GraduationCap, FileCheck, Briefcase, Home as HomeIcon,
  LogOut, Globe, Sparkles, Calculator, User, BookOpen, ChevronRight,
} from 'lucide-react';

const APP_NAME = 'udaan';
const APP_TAGLINE = 'the study abroad app for indian students';

const menuItems = [
  { name: 'Home',          path: '/dashboard',     icon: Home },
  { name: 'Study Tools',   path: '/ai-coach',      icon: BookOpen },
  { name: 'Universities',  path: '/universities',  icon: GraduationCap },
  { name: 'Housing',       path: '/housing',       icon: HomeIcon },
  { name: 'Visa Assistant',path: '/visa-chat',     icon: FileCheck },
  { name: 'Jobs',          path: '/jobs',          icon: Briefcase },
  { name: 'Finance',       path: '/finance',       icon: Calculator },
  { name: 'My Shortlist',  path: '/decision',      icon: Globe },
  { name: 'Profile',       path: '/profile',       icon: User },
];

export default function Layout() {
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

  return (
    <div className="flex min-h-screen">
      {/* ── Sidebar ── */}
      <aside className="w-56 bg-surface border-r border-surfaceBorder flex flex-col fixed h-screen z-20"
        style={{ boxShadow: '1px 0 0 #E2E8F0' }}>

        {/* Logo */}
        <div className="px-4 py-4 border-b border-surfaceBorder">
          <div className="flex items-center gap-2.5">
            {/* Udaan icon — stylised upward wing */}
            <div className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0"
              style={{ background: 'linear-gradient(135deg, #1E40AF 0%, #3B82F6 100%)' }}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                <path d="M12 3 C7 8 3 10 3 16 C7 14 10 13 12 15 C14 13 17 14 21 16 C21 10 17 8 12 3Z"
                  fill="white" fillOpacity="0.9"/>
                <path d="M12 15 L12 21" stroke="white" strokeWidth="2" strokeLinecap="round"/>
              </svg>
            </div>
            <div className="min-w-0">
              <p className="font-brand font-bold text-text leading-none tracking-wide"
                style={{ fontSize: '1.2rem', letterSpacing: '0.02em' }}>{APP_NAME}</p>
              <p className="text-[9px] text-muted mt-0.5 leading-tight">{APP_TAGLINE}</p>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-2 py-3 space-y-0.5 overflow-y-auto">
          {menuItems.map(({ name, path, icon: Icon }) => {
            const active = location.pathname === path;
            return (
              <Link
                key={path}
                to={path}
                className={`flex items-center gap-2.5 px-3 py-2 rounded-md text-sm font-medium transition-all ${
                  active
                    ? 'bg-lavendLight text-lavender'
                    : 'text-textSoft hover:bg-surfaceAlt hover:text-text'
                }`}
              >
                <Icon className={`w-4 h-4 flex-shrink-0 ${active ? 'text-lavender' : 'text-muted'}`} />
                <span>{name}</span>
                {active && <ChevronRight className="w-3 h-3 ml-auto text-lavender opacity-60" />}
              </Link>
            );
          })}
        </nav>

        {/* Logout */}
        <div className="px-2 py-3 border-t border-surfaceBorder">
          <button
            onClick={handleLogout}
            className="flex items-center gap-2.5 px-3 py-2 w-full rounded-md text-sm font-medium text-textSoft hover:bg-rose-50 hover:text-rose-600 transition-all"
          >
            <LogOut className="w-4 h-4 flex-shrink-0" />
            Sign out
          </button>
        </div>
      </aside>

      {/* ── Main content ── */}
      <main className="flex-1 ml-56 min-h-screen">
        <div className="max-w-5xl mx-auto px-6 py-6">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
