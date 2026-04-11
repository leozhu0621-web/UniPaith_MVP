import { Link } from "react-router-dom";

const Footer = () => (
  <footer className="bg-ink text-white py-14 px-4 sm:px-6 lg:px-8">
    <div className="max-w-6xl mx-auto">
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-8 mb-10">
        <div>
          <h4 className="text-lg mb-4">
            <span className="font-normal text-harbor">Uni</span>
            <span className="font-extrabold text-white">Paith</span>
          </h4>
          <p className="text-sm text-gray-400">Your private college advisor. Smart matching, applications, and guidance for students and institutions.</p>
        </div>
        <div>
          <h5 className="font-semibold mb-3 text-sm">Platform</h5>
          <ul className="space-y-2 text-sm text-gray-400">
            <li><Link to="/for-students" className="hover:text-harbor transition-colors">For Students</Link></li>
            <li><Link to="/for-institutions" className="hover:text-harbor transition-colors">For Institutions</Link></li>
            <li><Link to="/engine" className="hover:text-harbor transition-colors">AI Engine</Link></li>
            <li><Link to="/browse" className="hover:text-harbor transition-colors">Browse Programs</Link></li>
          </ul>
        </div>
        <div>
          <h5 className="font-semibold mb-3 text-sm">Company</h5>
          <ul className="space-y-2 text-sm text-gray-400">
            <li><Link to="/about" className="hover:text-harbor transition-colors">About</Link></li>
            <li><Link to="/pricing" className="hover:text-harbor transition-colors">Pricing</Link></li>
            <li><Link to="/blog" className="hover:text-harbor transition-colors">Blog</Link></li>
          </ul>
        </div>
        <div>
          <h5 className="font-semibold mb-3 text-sm">Legal</h5>
          <ul className="space-y-2 text-sm text-gray-400">
            <li><a href="#" className="hover:text-harbor transition-colors">Privacy Policy</a></li>
            <li><a href="#" className="hover:text-harbor transition-colors">Terms of Service</a></li>
          </ul>
        </div>
      </div>
      <div className="border-t border-white/10 pt-6 text-center text-sm text-gray-500">
        &copy; {new Date().getFullYear()} UniPaith. All rights reserved.
      </div>
    </div>
  </footer>
);

export default Footer;
