import { useState } from "react";
import { Link } from "react-router-dom";
import { Button } from "@/components/shadcn/button";
import { Menu, X } from "lucide-react";

const Navbar = () => {
  const [mobileOpen, setMobileOpen] = useState(false);

  const links = [
    { label: "For Students", to: "/for-students" },
    { label: "For Institutions", to: "/for-institutions" },
    { label: "AI Engine", to: "/engine" },
  ];

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-background/90 backdrop-blur-md border-b">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <Link to="/" className="text-2xl hover:scale-105 transition-transform">
            <span className="font-normal text-brand-slate-600">Uni</span>
            <span className="font-extrabold text-brand-slate-800">Paith</span>
          </Link>

          <div className="hidden md:flex items-center gap-6">
            {links.map((l) => (
              <Link key={l.to} to={l.to} className="story-link text-sm font-medium text-muted-foreground hover:text-foreground transition-colors">
                {l.label}
              </Link>
            ))}
            <Button variant="outline" size="sm" asChild>
              <Link to="/login">Log in</Link>
            </Button>
            <Button size="sm" className="bg-brand-amber-500 hover:bg-brand-amber-600 text-white" asChild>
              <Link to="/signup">Get Started</Link>
            </Button>
          </div>

          <button className="md:hidden text-foreground" onClick={() => setMobileOpen(!mobileOpen)}>
            {mobileOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>
      </div>

      {mobileOpen && (
        <div className="md:hidden bg-background border-b px-4 pb-4 space-y-3">
          {links.map((l) => (
            <Link key={l.to} to={l.to} onClick={() => setMobileOpen(false)} className="block text-sm font-medium text-muted-foreground hover:text-foreground">
              {l.label}
            </Link>
          ))}
          <div className="flex flex-col gap-2 pt-2">
            <Button variant="outline" size="sm" asChild>
              <Link to="/login" onClick={() => setMobileOpen(false)}>Log in</Link>
            </Button>
            <Button size="sm" className="bg-brand-amber-500 hover:bg-brand-amber-600 text-white" asChild>
              <Link to="/signup" onClick={() => setMobileOpen(false)}>Get Started</Link>
            </Button>
          </div>
        </div>
      )}
    </nav>
  );
};

export default Navbar;
