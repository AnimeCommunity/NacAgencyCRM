const BASE_URL = 'http://localhost:8000/api';

async function request(endpoint: string, options: RequestInit = {}) {
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  const response = await fetch(`${BASE_URL}${endpoint}`, { ...options, headers });
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || `Error en la petición: ${response.status}`);
  }
  
  if (response.status === 204) return null;
  return response.json();
}

export const apiService = {
  // clientes
  clientes: {
    getAll: () => request('/clients/'),
    create: (data: any) => request('/clients/', { method: 'POST', body: JSON.stringify(data) }),
    getInteracciones: (id: number) => request(`/clients/${id}/`),
  },

  // proyectos
  proyectos: {
    getAll: () => request('/projects/'),
    create: (data: any) => request('/projects/', { method: 'POST', body: JSON.stringify(data) }),
  },

  // cotizaciones
  cotizaciones: {
    getAll: () => request('/quotations/'),
    create: (data: any) => request('/quotations/', { method: 'POST', body: JSON.stringify(data) }),
  },

  // marketing
  marketing: {
    getTemplates: () => request('/marketing-templates/'),
    createTemplate: (data: any) => request('/marketing-templates/', { method: 'POST', body: JSON.stringify(data) }),
    getConfig: () => request('/marketing-config/'),
    saveConfig: (data: any) => request('/marketing-config/', { method: 'POST', body: JSON.stringify(data) }),
    updateConfig: (id: number, data: any) => request(`/marketing-config/${id}/`, { method: 'PUT', body: JSON.stringify(data) }),
    enviarCampana: (clienteId: number, plantillaId: number) => 
      request('/marketing/enviar-campana/', { 
        method: 'POST', 
        body: JSON.stringify({ cliente_id: clienteId, plantilla_id: plantillaId }) 
      }),
    // Analitica de marketing
    getStats: () => request('/marketing/stats/'),
    // Exportar Excel
    getExcelUrl: () => `${BASE_URL}/marketing/export-excel/`
  },

  // REPORTES GENERALES
  reportes: {
    getInformeGerencial: () => request('/reports/derencial/') 
  }
};