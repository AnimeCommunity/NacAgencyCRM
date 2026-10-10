export type UserRole = 'admin' | 'sales' | 'production';

export interface TokenPair {
  access: string;
  refresh: string;
}

export interface SessionClaims {
  user_id?: number;
  role?: UserRole;
  exp?: number;
  [key: string]: unknown;
}

export interface LoginInput {
  username: string;
  password: string;
}

export interface RegisterInput extends LoginInput {
  email: string;
  first_name: string;
  last_name: string;
}

export interface UserSummary {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
  email: string;
  role: UserRole;
  is_active: boolean;
}

export type ClientType = 'natural' | 'empresa';
export type ClientStatus = 'activo' | 'inactivo' | 'potencial';
export type ClientOrigin = 'web' | 'whatsapp' | 'redes' | 'referido' | 'otro';

export interface Client {
  id: number;
  tipo: ClientType;
  nombre: string;
  telefono: string | null;
  email: string;
  empresa: string | null;
  estado: ClientStatus;
  ciudad: string | null;
  origen: ClientOrigin;
  created_at: string;
  notas: string | null;
}

export type ClientInput = Omit<Client, 'id' | 'created_at'>;

export type InteractionType =
  | 'llamada'
  | 'correo_manual'
  | 'reunión'
  | 'seguimiento'
  | 'email_marketing'
  | 'whatsapp_link';

export type InteractionOutcome =
  | 'sin_definir'
  | 'contactado'
  | 'sin_respuesta'
  | 'interesado'
  | 'no_interesado'
  | 'reunion_agendada'
  | 'cerrado';

export interface Interaction {
  id: number;
  cliente: number;
  tipo: InteractionType;
  resultado: InteractionOutcome;
  descripcion: string;
  created_at: string;
  created_by: number | null;
}

export interface InteractionInput {
  cliente: number;
  tipo: InteractionType;
  resultado: InteractionOutcome;
  descripcion: string;
}

export type ProjectStatus = 'propuesta' | 'aprobado' | 'en_proceso' | 'finalizado' | 'cancelado';
export type EventType = 'concierto' | 'show' | 'streaming' | 'fiesta' | 'sesion_fotografica' | 'otro';

export interface Project {
  id: number;
  cliente: Client;
  responsable: UserSummary | null;
  nombre: string;
  descripcion: string;
  tipo_evento: EventType;
  fecha_inicio: string;
  fecha_fin: string;
  presupuesto_estimado: string;
  pagado: boolean;
  fecha_pago: string | null;
  estado: ProjectStatus;
  created_at: string;
}

export interface ProjectInput {
  cliente: number;
  responsable: number;
  nombre: string;
  descripcion: string;
  tipo_evento: EventType;
  fecha_inicio: string;
  fecha_fin: string;
  presupuesto_estimado: number;
  pagado: boolean;
  fecha_pago: string | null;
  estado: ProjectStatus;
}

export interface ProjectMutationResponse extends Omit<Project, 'cliente' | 'responsable'> {
  cliente: number;
  responsable: number | null;
}

export interface QuotationItem {
  id: number;
  descripcion: string;
  cantidad: number;
  precio_unitario: string;
  total: string;
}

export interface QuotationItemInput {
  descripcion: string;
  cantidad: number;
  precio_unitario: number;
}

export type QuotationStatus = 'enviada' | 'aceptada' | 'rechazada' | 'vencida';

export interface Quotation {
  id: number;
  projecto: number;
  numero: string;
  subtotal: string;
  impuestos: string;
  total: string;
  estado: QuotationStatus;
  created_at: string;
  fecha_vencimiento: string;
  notas: string | null;
  items: QuotationItem[];
}

export interface QuotationCreateInput {
  projecto: number;
  estado: QuotationStatus;
  fecha_vencimiento: string;
  notas: string;
  items: QuotationItemInput[];
}

export type QuotationUpdateInput = Partial<
  Pick<Quotation, 'estado' | 'fecha_vencimiento' | 'notas'>
> & { items?: QuotationItemInput[] };

export type MarketingTemplateType = 'email' | 'whatsapp';

export interface MarketingTemplate {
  id: number;
  nombre: string;
  tipo: MarketingTemplateType;
  tipo_display: string;
  asunto: string | null;
  contenido: string;
  created_at: string;
}

export interface MarketingTemplateInput {
  nombre: string;
  tipo: MarketingTemplateType;
  asunto: string;
  contenido: string;
}

export interface SMTPConfig {
  id: number;
  email_usuario: string;
  servidor_host: string;
  puerto: number;
  use_tls: boolean;
  password_configurada: boolean;
}

export interface SMTPConfigInput {
  email_usuario: string;
  email_password?: string;
  servidor_host: string;
  puerto: number;
  use_tls: boolean;
}

export interface CampaignResponse {
  status: string;
  url?: string;
}

export interface MarketingStats {
  origenes: Array<{ origen: ClientOrigin; total: number }>;
  ejecutivos: Array<{
    projecto__responsable__username: string | null;
    total_cotizaciones: number;
    monto_proyectado: string | null;
  }>;
  resumen_ventas: {
    total_ingresos: string | number;
    cantidad_ventas: number;
  };
}

export interface ReportFilters {
  desde?: string;
  hasta?: string;
  cliente?: number;
  responsable?: number;
  estado_proyecto?: ProjectStatus;
  tipo_evento?: EventType;
}

export interface ManagementReport {
  filtros: ReportFilters;
  resumen_conversion: {
    total: number;
    aceptadas: number;
    pendientes: number;
    rechazadas: number;
    vencidas: number;
    tasa_exito_porcentaje: number;
  };
  clientes_conversion: {
    total_clientes: number;
    clientes_que_cotizaron: number;
    clientes_que_concretaron: number;
    clientes_que_pagaron: number;
    tasa_cliente_a_cotizacion: number;
    tasa_cotizacion_a_cierre: number;
    tasa_cierre_a_pago: number;
  };
  resumen_financiero: {
    ingresos_aceptados: string | number;
    ingresos_pagados: string | number;
    saldo_por_cobrar: string | number;
  };
  clientes_por_estado: Array<{ estado: ClientStatus; total: number }>;
  proyectos_por_estado: Array<{ estado: ProjectStatus; total: number }>;
  cotizaciones_por_estado: Array<{ estado: QuotationStatus; total: number }>;
  interacciones_por_resultado: Array<{ resultado: InteractionOutcome; total: number }>;
  ingresos_por_tipo_evento: Array<{
    tipo_evento: EventType;
    cantidad_proyectos: number;
    total_generado: string;
  }>;
  top_5_clientes: Array<{
    nombre: string;
    total_invertido: string;
  }>;
  clientes_por_proyecto: Array<{
    proyecto_id: number;
    proyecto_nombre: string;
    estado: ProjectStatus;
    pagado: boolean;
    cliente_id: number;
    cliente_nombre: string;
    cotizaciones: number;
    cotizaciones_aceptadas: number;
  }>;
  actividad_mensual: Array<{
    periodo: string;
    proyectos: number;
    cotizaciones: number;
    interacciones: number;
    ingresos_aceptados: string | number;
  }>;
  actividad_semanal: Array<{
    periodo: string;
    proyectos: number;
    cotizaciones: number;
    interacciones: number;
    ingresos_aceptados: string | number;
  }>;
}

type ErrorPayload = Record<string, unknown> | unknown[] | string | null;

export class ApiError extends Error {
  status: number;
  data: ErrorPayload;

  constructor(message: string, status: number, data: ErrorPayload = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

const configuredUrl = process.env.NEXT_PUBLIC_API_URL?.trim();
if (!configuredUrl) {
  throw new Error('NEXT_PUBLIC_API_URL debe definirse al iniciar o compilar el frontend.');
}

function normalizeApiBase(value: string): string {
  const withoutTrailingSlash = value.replace(/\/+$/, '');
  return withoutTrailingSlash.endsWith('/api')
    ? withoutTrailingSlash
    : `${withoutTrailingSlash}/api`;
}

export const API_BASE_URL = normalizeApiBase(configuredUrl);

const ACCESS_KEY = 'access_token';
const REFRESH_KEY = 'refresh_token';
let refreshPromise: Promise<string | null> | null = null;

function getStorageValue(key: string): string | null {
  return typeof window === 'undefined' ? null : window.localStorage.getItem(key);
}

export function saveSessionTokens(tokens: TokenPair | { access: string; refresh?: string }): void {
  if (typeof window === 'undefined') return;
  window.localStorage.setItem(ACCESS_KEY, tokens.access);
  if (tokens.refresh) window.localStorage.setItem(REFRESH_KEY, tokens.refresh);
  window.dispatchEvent(new Event('crm-auth-changed'));
}

export function clearSessionTokens(): void {
  if (typeof window === 'undefined') return;
  window.localStorage.removeItem(ACCESS_KEY);
  window.localStorage.removeItem(REFRESH_KEY);
  window.dispatchEvent(new Event('crm-auth-changed'));
}

function decodeJwt(token: string | null): SessionClaims | null {
  if (!token || typeof window === 'undefined') return null;
  try {
    const payload = token.split('.')[1];
    if (!payload) return null;
    const normalized = payload.replace(/-/g, '+').replace(/_/g, '/');
    const padded = normalized.padEnd(Math.ceil(normalized.length / 4) * 4, '=');
    return JSON.parse(window.atob(padded)) as SessionClaims;
  } catch {
    return null;
  }
}

export function getSessionClaims(): SessionClaims | null {
  return decodeJwt(getStorageValue(ACCESS_KEY));
}

export function hasStoredSession(): boolean {
  return Boolean(getStorageValue(ACCESS_KEY));
}

function flattenError(data: ErrorPayload): string | null {
  if (!data) return null;
  if (typeof data === 'string') return data;
  if (Array.isArray(data)) {
    const messages = data.map((item) => flattenError(item as ErrorPayload)).filter(Boolean);
    return messages.length ? messages.join(' ') : null;
  }

  for (const key of ['detail', 'error', 'message', 'non_field_errors']) {
    if (key in data) {
      const message = flattenError(data[key] as ErrorPayload);
      if (message) return message;
    }
  }

  const messages = Object.entries(data)
    .map(([field, value]) => {
      const message = flattenError(value as ErrorPayload);
      return message ? `${field}: ${message}` : null;
    })
    .filter(Boolean);
  return messages.length ? messages.join(' ') : null;
}

export function getErrorMessage(error: unknown, fallback = 'Ocurrió un error inesperado.'): string {
  return error instanceof Error && error.message ? error.message : fallback;
}

async function readError(response: Response): Promise<ApiError> {
  const data = (await response.json().catch(() => null)) as ErrorPayload;
  const message = flattenError(data) || `La solicitud falló (${response.status}).`;
  return new ApiError(message, response.status, data);
}

function redirectToLogin(): void {
  clearSessionTokens();
}

async function refreshAccessToken(): Promise<string | null> {
  if (refreshPromise) return refreshPromise;

  refreshPromise = (async () => {
    const refresh = getStorageValue(REFRESH_KEY);
    if (!refresh) return null;

    try {
      const response = await fetch(`${API_BASE_URL}/token/refresh/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh }),
      });
      if (!response.ok) return null;

      const tokens = (await response.json()) as { access: string; refresh?: string };
      saveSessionTokens(tokens);
      return tokens.access;
    } catch {
      return null;
    } finally {
      refreshPromise = null;
    }
  })();

  return refreshPromise;
}

interface RequestOptions extends RequestInit {
  skipAuth?: boolean;
  retryAuth?: boolean;
}

async function fetchWithAuth(endpoint: string, options: RequestOptions = {}): Promise<Response> {
  const { skipAuth = false, retryAuth = true, ...fetchOptions } = options;
  const headers = new Headers(fetchOptions.headers);
  const access = skipAuth ? null : getStorageValue(ACCESS_KEY);

  if (fetchOptions.body && !(fetchOptions.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }
  if (access) headers.set('Authorization', `Bearer ${access}`);

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${endpoint}`, { ...fetchOptions, headers });
  } catch {
    throw new ApiError('No fue posible conectar con el servidor.', 0);
  }

  if (response.status === 401 && !skipAuth && retryAuth) {
    const refreshedAccess = await refreshAccessToken();
    if (refreshedAccess) {
      headers.set('Authorization', `Bearer ${refreshedAccess}`);
      response = await fetch(`${API_BASE_URL}${endpoint}`, { ...fetchOptions, headers });
    } else {
      redirectToLogin();
    }
  }

  if (response.status === 401 && !skipAuth) redirectToLogin();
  return response;
}

async function request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const response = await fetchWithAuth(endpoint, options);
  if (!response.ok) throw await readError(response);
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

async function requestBlob(endpoint: string): Promise<Blob> {
  const response = await fetchWithAuth(endpoint);
  if (!response.ok) throw await readError(response);
  return response.blob();
}

function withQuery(endpoint: string, params: object): string {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== '') query.set(key, String(value));
  });
  const serialized = query.toString();
  return serialized ? `${endpoint}?${serialized}` : endpoint;
}

export const apiService = {
  auth: {
    login: async (data: LoginInput) => {
      const tokens = await request<TokenPair>('/token/', {
        method: 'POST',
        body: JSON.stringify(data),
        skipAuth: true,
      });
      saveSessionTokens(tokens);
      return tokens;
    },
    register: (data: RegisterInput) =>
      request<UserSummary>('/register/', {
        method: 'POST',
        body: JSON.stringify(data),
        skipAuth: true,
      }),
    logout: async () => {
      try {
        const access = await refreshAccessToken();
        const refresh = getStorageValue(REFRESH_KEY);
        if (access && refresh) {
          await request<void>('/logout/', {
            method: 'POST',
            body: JSON.stringify({ refresh }),
            retryAuth: false,
          });
        }
      } finally {
        clearSessionTokens();
      }
    },
  },
  usuarios: {
    getAll: () => request<UserSummary[]>('/users/'),
    update: (id: number, data: Partial<Pick<UserSummary, 'role' | 'is_active'>>) =>
      request<UserSummary>(`/users/${id}/`, { method: 'PATCH', body: JSON.stringify(data) }),
  },
  clientes: {
    getAll: () => request<Client[]>('/clients/'),
    getById: (id: number) => request<Client>(`/clients/${id}/`),
    create: (data: ClientInput) =>
      request<Client>('/clients/', { method: 'POST', body: JSON.stringify(data) }),
    update: (id: number, data: Partial<ClientInput>) =>
      request<Client>(`/clients/${id}/`, { method: 'PATCH', body: JSON.stringify(data) }),
    remove: (id: number) => request<void>(`/clients/${id}/`, { method: 'DELETE' }),
    exportExcel: () => requestBlob('/marketing/export-excel/'),
  },
  interacciones: {
    getAll: (clientId?: number) =>
      request<Interaction[]>(`/interactions/${clientId ? `?cliente=${clientId}` : ''}`),
    create: (data: InteractionInput) =>
      request<Interaction>('/interactions/', { method: 'POST', body: JSON.stringify(data) }),
    update: (id: number, data: Partial<InteractionInput>) =>
      request<Interaction>(`/interactions/${id}/`, { method: 'PATCH', body: JSON.stringify(data) }),
    remove: (id: number) => request<void>(`/interactions/${id}/`, { method: 'DELETE' }),
    exportExcel: (clientId?: number) =>
      requestBlob(`/interactions/export/${clientId ? `?cliente=${clientId}` : ''}`),
  },
  proyectos: {
    getAll: () => request<Project[]>('/projects/'),
    create: (data: ProjectInput) =>
      request<ProjectMutationResponse>('/projects/', { method: 'POST', body: JSON.stringify(data) }),
    update: (id: number, data: Partial<ProjectInput>) =>
      request<ProjectMutationResponse>(`/projects/${id}/`, { method: 'PATCH', body: JSON.stringify(data) }),
    cancel: (id: number) =>
      request<Project>(`/projects/${id}/cancel/`, { method: 'POST' }),
  },
  cotizaciones: {
    getAll: () => request<Quotation[]>('/quotations/'),
    create: (data: QuotationCreateInput) =>
      request<Quotation>('/quotations/', { method: 'POST', body: JSON.stringify(data) }),
    update: (id: number, data: QuotationUpdateInput) =>
      request<Quotation>(`/quotations/${id}/`, { method: 'PATCH', body: JSON.stringify(data) }),
    exportExcel: () => requestBlob('/quotations/export/'),
  },
  marketing: {
    getTemplates: () => request<MarketingTemplate[]>('/marketing/templates/'),
    createTemplate: (data: MarketingTemplateInput) =>
      request<MarketingTemplate>('/marketing/templates/', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    getConfig: () => request<SMTPConfig[]>('/marketing/config-smtp/'),
    saveConfig: (data: SMTPConfigInput) =>
      request<SMTPConfig>('/marketing/config-smtp/', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    updateConfig: (id: number, data: Partial<SMTPConfigInput>) =>
      request<SMTPConfig>(`/marketing/config-smtp/${id}/`, {
        method: 'PATCH',
        body: JSON.stringify(data),
      }),
    testConfig: (id: number) =>
      request<{ status: string }>(`/marketing/config-smtp/${id}/test-connection/`, {
        method: 'POST',
      }),
    enviarCampana: (clienteId: number, plantillaId: number) =>
      request<CampaignResponse>('/marketing/enviar-campana/', {
        method: 'POST',
        body: JSON.stringify({ cliente_id: clienteId, plantilla_id: plantillaId }),
      }),
    getStats: () => request<MarketingStats>('/marketing/stats/'),
  },
  reportes: {
    getInformeGerencial: (filters: ReportFilters = {}) =>
      request<ManagementReport>(withQuery('/reports/gerencial/', filters)),
    exportInformeGerencial: (filters: ReportFilters = {}) =>
      requestBlob(withQuery('/reports/gerencial/export/', filters)),
  },
};
