import { useState } from "react";
import { Button } from "@/components/shadcn/button";
import { Menu, X } from "lucide-react";

const Navbar = () => {
  const [mobileOpen, setMobileOpen] = useState(false);

  const links = [
    { label: "For Students", href: "#students" },
    { label: "For Institutions", href: "#institutions" },
    { label: "How It Works", href: "#flywheel" },
    { label: "AI Features", href: "#ai-features" },
  ];

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-background/90 backdrop-blur-md border-b">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <a href="#" className="text-2xl hover:scale-105 transition-transform">
            <span className="font-normal text-forest-600">Uni</span>
            <span className="font-extrabold text-forest-800">Paith</span>
          </a>

          <div className="hidden md:flex items-center gap-6">
            {links.map((l) => (
              <a key={l.href} href={l.href} className="story-link text-sm font-medium text-muted-foreground hover:text-foreground transition-colors">
                {l.label}
              </a>
            ))}
            <Button variant="outline" size="sm" asChild>
              <a href="#cta">Request a Demo</a>
            </Button>
            <Button size="sm" asChild>
              <a href="#cta">Join the Waitlist</a>
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
            <a key={l.href} href={l.href} onClick={() => setMobileOpen(false)} className="block text-sm font-medium text-muted-foreground hover:text-foreground">
              {l.label}
            </a>
          ))}
          <div className="flex flex-col gap-2 pt-2">
            <Button variant="outline" size="sm" asChild>
              <a href="#cta">Request a Demo</a>
            </Button>
            <Button size="sm" asChild>
              <a href="#cta">Join the Waitlist</a>
            </Button>
          </div>
        </div>
      )}
    </nav>
  );
};

export default Navbar;
