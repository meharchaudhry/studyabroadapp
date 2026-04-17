import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom';
import {
  Home, GraduationCap, FileCheck, Briefcase, Home as HomeIcon, LogOut, ChevronRight, Globe, Activity, User
} from 'lucide-react';

const menuItems = [
  { name: 'Dashboard',    path: '/dashboard',     icon: Home },
  { name: 'Universities', path: '/universities',  icon: GraduationCap },
  { name: 'Housing',      path: '/housing',       icon: HomeIcon },
  { name: 'Visa Guide',   path: '/visa-chat',     icon: FileCheck },
  { name: 'Jobs',         path: '/jobs',          icon: Briefcase },
  { name: 'RAG Eval',     path: '/evaluation',    icon: Activity },
  { name: 'Profile',      path: '/profile',       icon: User },
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
      <aside className="w-60 bg-surface border-r border-surfaceBorder flex flex-col fixed h-screen z-20 shadow-soft">
        {/* Logo */}
        <div className="px-6 py-5 border-b border-surfaceBorder">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 bg-lavender rounded-lg flex items-center justify-center shadow-sm">
              <Globe className="w-4.5 h-4.5 text-white w-[18px] h-[18px]" />
            </div>
            <div>
              <h1 className="text-sm font-bold text-text leading-none">StudyPathway</h1>
              <p className="text-[10px] text-muted mt-0.5">For Indian Students</p>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
          {menuItems.map(({ name, path, icon: Icon }) => {
            const active = location.pathname === path;
            return (
              <Link
                key={path}
                to={path}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${
                  active
                    ? 'bg-lavendLight text-lavender'
                    : 'text-textSoft hover:bg-surfaceAlt hover:text-text'
                }`}
              >
                <Icon className={`w-4.5 h-4.5 w-[18px] h-[18px] ${active ? 'text-lavender' : ''}`} />
                {name}
                {active && <ChevronRight className="w-3.5 h-3.5 ml-auto text-lavender" />}
              </Link>
            );
          })}
        </nav>

        {/* Logout */}
        <div className="px-3 py-4 border-t border-surfaceBorder">
          <button
            onClick={handleLogout}
            className="flex items-center gap-3 px-3 py-2.5 w-full rounded-xl text-sm font-medium text-textSoft hover:bg-rose/10 hover:text-rose transition-all"
          >
            <LogOut className="w-[18px] h-[18px]" />
            Sign Out
          </button>
        </div>
      </aside>

      {/* ── Main ── */}
      <main className="flex-1 ml-60 p-6 min-h-screen">
        <div className="max-w-6xl mx-auto">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
