import { Outlet } from 'react-router-dom'
import Navbar from '../landing/Navbar'
import Footer from '../landing/Footer'

export default function PublicLayout() {
  return (
    <div className="min-h-screen">
      <Navbar />
      <main>
        <Outlet />
      </main>
      <Footer />
    </div>
  )
}
