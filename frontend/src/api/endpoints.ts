export const endpoints = {
  health: '/health',
  experiments: {
    list: '/v1/experiments',
    search: '/v1/experiments/search',
    byId: (experimentId: string) => `/v1/experiments/${encodeURIComponent(experimentId)}`,
  },
  hardware: {
    list: '/v1/hardware',
    search: '/v1/hardware/search',
    byId: (hardwareId: string) => `/v1/hardware/${encodeURIComponent(hardwareId)}`,
  },
  relationships: {
    list: '/v1/relationships',
    search: '/v1/relationships/search',
    byId: (relationshipId: string) => `/v1/relationships/${encodeURIComponent(relationshipId)}`,
    byExperiment: (experimentId: string) => `/v1/relationships/by-experiment/${encodeURIComponent(experimentId)}`,
    byHardware: (hardwareId: string) => `/v1/relationships/by-hardware/${encodeURIComponent(hardwareId)}`,
  },
  sources: {
    list: '/v1/sources',
    search: '/v1/sources/search',
    byId: (sourceId: string) => `/v1/sources/${encodeURIComponent(sourceId)}`,
    verification: (sourceId: string) => `/v1/sources/${encodeURIComponent(sourceId)}/verification`,
  },
  comparisons: {
    experiments: '/v1/comparisons/experiments',
    hardware: '/v1/comparisons/hardware',
    measurements: '/v1/comparisons/measurements',
  },
  rankings: {
    create: '/v1/rankings',
  },
  missionRelevance: {
    byExperiment: (experimentId: string) => `/v1/mission-relevance/experiments/${encodeURIComponent(experimentId)}`,
    byHardware: (hardwareId: string) => `/v1/mission-relevance/hardware/${encodeURIComponent(hardwareId)}`,
  },
  fireSafety: {
    insights: '/v1/fire-safety/insights',
    prevention: '/v1/fire-safety/prevention',
    detection: '/v1/fire-safety/detection',
    suppression: '/v1/fire-safety/suppression',
    summary: '/v1/fire-safety/summary',
    byExperiment: (experimentId: string) => `/v1/fire-safety/experiments/${encodeURIComponent(experimentId)}`,
    byHardware: (hardwareId: string) => `/v1/fire-safety/hardware/${encodeURIComponent(hardwareId)}`,
  },
}
