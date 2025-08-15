export interface ProcessStep {
  id: number;
  name: string;
  status: 'pending' | 'running' | 'completed' | 'error';
  description: string;
  result?: OptimizationResult | AnalysisResult | Record<string, unknown>;
  details?: Record<string, unknown>;
}

export interface AnalysisResult {
  event_type: string;
  severity: string;
  confidence: number;
  weights: Record<string, WeightConfig>;
  timestamp?: string;
}

export interface WeightConfig {
  cancel: number;
  delay: number;
  late_pax: number;
  revenue: number;
  change_time: number;
  change_aircraft: number;
  cancel_flight: number;
  change_airport: number;
  change_nature: number;
  add_flight: number;
}

export interface OptimizationResult {
  chosen_plan_name: string;
  solutions: Record<string, FlightAdjustment[]>;
  summary: OptimizationSummary;
  execution_status: string;
}

export interface FlightAdjustment {
  flight_number: string;
  adjustment_action: string;
  status: string;
  additional_delay_minutes: number;
  adjusted_departure_time: string | null;
  reason: string;
}

export interface OptimizationSummary {
  total_flights: number;
  cancelled_flights: number;
  delayed_flights: number;
  normal_flights: number;
  total_delay_minutes: number;
  cost_saving: number;
}

export interface DataStatistics {
  total_flights: number;
  normal_flights: number;
  affected_flights: number;
}

export interface WeightConfirmation {
  show: boolean;
  weights: Record<string, WeightConfig> | null;
  confirmed: boolean;
  data?: AnalysisResult;
}

export interface FileInfo {
  cdm_files?: Array<{
    name: string;
    size: number;
    modified: string;
  }>;
  constraint_files?: Array<{
    name: string;
    exists: boolean;
    size?: number;
    modified?: string;
  }>;
}

export interface FilePreview {
  filename: string;
  content: string;
}
