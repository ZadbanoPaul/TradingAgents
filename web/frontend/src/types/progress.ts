export type ProgressRow = Record<string, unknown> & {
  ts?: string;
  type?: string;
  title?: string;
  lines?: string[];
};
