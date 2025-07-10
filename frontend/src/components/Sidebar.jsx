import { NavLink } from 'react-router-dom'

const links = [
  { to: '/dashboard',         label: 'Dashboard' },
  { to: '/financial-analysis',label: 'Financial Analysis' },
  { to: '/risk-assessment',   label: 'Risk Assessment' },
  { to: '/operational-efficiency', label: 'Operational Efficiency' },
  { to: '/DemoGraphic',       label: 'DemoGraphic' },
  { to: '/CustomerInsights',       label: 'Customer Insights' },
  { to: '/reports',           label: 'Reports' },
]

export default function Sidebar() {
  return (
    <nav className="w-56 bg-[#001f3f] text-white flex flex-col py-4">
      <div className="text-center font-bold mb-4">Analytics 360</div>
      <ul className="space-y-1">
        {links.map((link, i) => (
          <li key={i}>
            <NavLink
              to={link.to}
              className={({ isActive }) =>
                `flex items-center px-4 py-2 rounded-lg transition ${
                  isActive
                    ? 'bg-[#002b5c] text-white'
                    : 'text-gray-300 hover:bg-[#002b5c]'
                }`
              }
            >
              <span className="w-6 text-center">{i + 1}</span>
              <span className="ml-2">{link.label}</span>
            </NavLink>
          </li>
        ))}
      </ul>
    </nav>
  )
}
