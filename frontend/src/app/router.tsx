import { createBrowserRouter } from 'react-router'
import { AppLayout } from '../components/layout/AppLayout'
import { CompareRankPage } from '../pages/CompareRankPage'
import { ExperimentExplorerPage } from '../pages/ExperimentExplorerPage'
import { FireSafetyPage } from '../pages/FireSafetyPage'
import { MissionRelevancePage } from '../pages/MissionRelevancePage'
import { NotFoundPage } from '../pages/NotFoundPage'
import { OverviewPage } from '../pages/OverviewPage'
import { ResearchAssistantPage } from '../pages/ResearchAssistantPage'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppLayout />,
    children: [
      { index: true, element: <OverviewPage /> },
      { path: 'experiments', element: <ExperimentExplorerPage /> },
      { path: 'compare', element: <CompareRankPage /> },
      { path: 'fire-safety', element: <FireSafetyPage /> },
      { path: 'mission-relevance', element: <MissionRelevancePage /> },
      { path: 'research-assistant', element: <ResearchAssistantPage /> },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
])
