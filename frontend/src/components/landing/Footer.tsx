import { Link } from "react-router-dom";

const Footer = () => (
  <footer className="bg-brand-slate-900 text-background py-14 px-4 sm:px-6 lg:px-8">
    <div className="max-w-6xl mx-auto">
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-8 mb-10">
        <div>
          <h4 className="text-lg mb-4">
            <span className="font-normal text-brand-slate-200">Uni</span>
            <span className="font-extrabold text-white">Paith</span>
          </h4>
          <p className="text-sm text-background/60">Apply once, go anywhere. AI-powered admissions for a connected world.</p>
        </div>
        <div>
          <h5 className="font-semibold mb-3 text-sm">Platform</h5>
          <ul className="space-y-2 text-sm text-background/60">
            <li><Link to="/for-students" className="hover:text-brand-amber-400 transition-colors">For Students</Link></li>
            <li><Link to="/for-institutions" className="hover:text-brand-amber-400 transition-colors">For Institutions</Link></li>
            <li><Link to="/engine" className="hover:text-brand-amber-400 transition-colors">AI Engine</Link></li>
          </ul>
        </div>
        <div>
          <h5 className="font-semibold mb-3 text-sm">Account</h5>
          <ul className="space-y-2 text-sm text-background/60">
            <li><Link to="/login" className="hover:text-brand-amber-400 transition-colors">Log in</Link></li>
            <li><Link to="/signup" className="hover:text-brand-amber-400 transition-colors">Sign up</Link></li>
          </ul>
        </div>
        <div>
          <h5 className="font-semibold mb-3 text-sm">Legal</h5>
          <ul className="space-y-2 text-sm text-background/60">
            <li><a href="#" className="hover:text-brand-amber-400 transition-colors">Privacy Policy</a></li>
            <li><a href="#" className="hover:text-brand-amber-400 transition-colors">Terms of Service</a></li>
          </ul>
        </div>
      </div>
      <div className="border-t border-background/20 pt-6 text-center text-sm text-background/50">
        &copy; {new Date().getFullYear()} UniPaith. All rights reserved.
      </div>
    </div>
  </footer>
);

export default Footer;
