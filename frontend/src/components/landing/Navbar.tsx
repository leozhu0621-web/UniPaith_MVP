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
    { label: "Pricing", to: "/pricing" },
    { label: "About", to: "/about" },
  ];

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-offwhite/90 backdrop-blur-md border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <Link to="/" className="text-2xl hover:scale-105 transition-transform">
            <span className="font-normal text-student">Uni</span>
            <span className="font-extrabold text-charcoal">Paith</span>
          </Link>

          <div className="hidden md:flex items-center gap-6">
            {links.map((l) => (
              <Link key={l.to} to={l.to} className="text-sm font-medium text-gray-500 hover:text-charcoal transition-colors">
                {l.label}
              </Link>
            ))}
            <Button variant="outline" size="sm" className="border-gray-300 text-charcoal hover:bg-student-mist" asChild>
              <Link to="/login">Log in</Link>
            </Button>
            <Button size="sm" className="bg-student hover:bg-student-hover text-white" asChild>
              <Link to="/signup">Get Started</Link>
            </Button>
          </div>

          <button className="md:hidden text-charcoal" onClick={() => setMobileOpen(!mobileOpen)}>
            {mobileOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>
      </div>

      {mobileOpen && (
        <div className="md:hidden bg-offwhite border-b border-gray-200 px-4 pb-4 space-y-3">
          {links.map((l) => (
            <Link key={l.to} to={l.to} onClick={() => setMobileOpen(false)} className="block text-sm font-medium text-gray-500 hover:text-charcoal">
              {l.label}
            </Link>
          ))}
          <div className="flex flex-col gap-2 pt-2">
            <Button variant="outline" size="sm" className="border-gray-300 text-charcoal" asChild>
              <Link to="/login" onClick={() => setMobileOpen(false)}>Log in</Link>
            </Button>
            <Button size="sm" className="bg-student hover:bg-student-hover text-white" asChild>
              <Link to="/signup" onClick={() => setMobileOpen(false)}>Get Started</Link>
            </Button>
          </div>
        </div>
      )}
    </nav>
  );
};

export default Navbar;
