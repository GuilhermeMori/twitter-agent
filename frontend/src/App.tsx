import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import ConfigurationPage from './pages/ConfigurationPage'
import CampaignCreationPage from './pages/CampaignCreationPage'
import CampaignHistoryPage from './pages/CampaignHistoryPage'
import CampaignDetailPage from './pages/CampaignDetailPage'
import AssistantListPage from './pages/AssistantListPage'
import AssistantEditPage from './pages/AssistantEditPage'
import PersonaListPage from './pages/PersonaListPage'
import PersonaDetailPage from './pages/PersonaDetailPage'
import PersonaCreatePage from './pages/PersonaCreatePage'
import PersonaEditPage from './pages/PersonaEditPage'

import { NotificationProvider } from './contexts/NotificationContext'

export default function App() {
  return (
    <NotificationProvider>
      <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/history" replace />} />
          <Route path="configuration" element={<ConfigurationPage />} />
          <Route path="campaigns" element={<Navigate to="/history" replace />} />
          <Route path="campaigns/new" element={<CampaignCreationPage />} />
          <Route path="campaigns/:id" element={<CampaignDetailPage />} />
          <Route path="history" element={<CampaignHistoryPage />} />
          {/* Assistants */}
          <Route path="assistants" element={<AssistantListPage />} />
          <Route path="assistants/:id/edit" element={<AssistantEditPage />} />
          {/* Communication Styles (also accessible via /personas for backward compat) */}
          <Route path="communication-styles" element={<PersonaListPage />} />
          <Route path="communication-styles/create" element={<PersonaCreatePage />} />
          <Route path="communication-styles/:id" element={<PersonaDetailPage />} />
          <Route path="communication-styles/:id/edit" element={<PersonaEditPage />} />
          {/* Legacy persona routes redirect */}
          <Route path="personas" element={<PersonaListPage />} />
          <Route path="personas/create" element={<PersonaCreatePage />} />
          <Route path="personas/:id" element={<PersonaDetailPage />} />
          <Route path="personas/:id/edit" element={<PersonaEditPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </NotificationProvider>
  )
}
