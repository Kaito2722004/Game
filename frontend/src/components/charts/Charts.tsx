import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { CHART_COLORS } from "@/utils/game";

const AXIS_STYLE = { fontSize: 11, fill: "#64748b" } as const;
const GRID_STROKE = "#e2e8f0";

/** Recharts hands the formatter a loose ValueType; coerce it once, here. */
function toNumber(value: unknown): number {
  const parsed = typeof value === "number" ? value : Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

const TOOLTIP_STYLE = {
  borderRadius: 8,
  border: "1px solid #e2e8f0",
  fontSize: 12,
  boxShadow: "0 4px 12px rgba(15, 23, 42, 0.08)",
} as const;

export interface CategoryDatum {
  label: string;
  value: number;
  /** Optional per-bar colour, e.g. green for cooperation. */
  color?: string;
}

interface CategoryBarChartProps {
  data: CategoryDatum[];
  xLabel: string;
  yLabel: string;
  color?: string;
  /** Format for the axis and tooltip, e.g. percentages. */
  formatter?: (value: number) => string;
  domain?: [number, number];
}

/** Vertical bars for a single measure across categories (strategies, rounds). */
export function CategoryBarChart({
  data,
  xLabel,
  yLabel,
  color = CHART_COLORS.neutral,
  formatter,
  domain,
}: CategoryBarChartProps) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data} margin={{ top: 8, right: 12, bottom: 28, left: 4 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={GRID_STROKE} vertical={false} />
        <XAxis
          dataKey="label"
          tick={AXIS_STYLE}
          interval={0}
          angle={-20}
          textAnchor="end"
          height={56}
          label={{ value: xLabel, position: "insideBottom", offset: -18, style: AXIS_STYLE }}
        />
        <YAxis
          tick={AXIS_STYLE}
          domain={domain}
          tickFormatter={formatter}
          label={{ value: yLabel, angle: -90, position: "insideLeft", style: AXIS_STYLE }}
        />
        <Tooltip
          contentStyle={TOOLTIP_STYLE}
          formatter={(value: unknown) => {
            const numeric = toNumber(value);
            return [formatter ? formatter(numeric) : numeric, yLabel];
          }}
        />
        <Bar dataKey="value" name={yLabel} radius={[4, 4, 0, 0]}>
          {data.map((entry, index) => (
            <Cell key={index} fill={entry.color ?? color} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

export interface SeriesConfig {
  key: string;
  name: string;
  color: string;
}

interface MultiLineChartProps {
  data: Array<Record<string, number | string>>;
  xKey: string;
  series: SeriesConfig[];
  xLabel: string;
  yLabel: string;
  formatter?: (value: number) => string;
  domain?: [number, number];
}

/** One or more lines over rounds: cumulative payoff, cooperation over time. */
export function MultiLineChart({
  data,
  xKey,
  series,
  xLabel,
  yLabel,
  formatter,
  domain,
}: MultiLineChartProps) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={data} margin={{ top: 8, right: 16, bottom: 24, left: 4 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={GRID_STROKE} />
        <XAxis
          dataKey={xKey}
          tick={AXIS_STYLE}
          label={{ value: xLabel, position: "insideBottom", offset: -14, style: AXIS_STYLE }}
        />
        <YAxis
          tick={AXIS_STYLE}
          domain={domain}
          tickFormatter={formatter}
          label={{ value: yLabel, angle: -90, position: "insideLeft", style: AXIS_STYLE }}
        />
        <Tooltip
          contentStyle={TOOLTIP_STYLE}
          formatter={(value: unknown, name: unknown) => {
            const numeric = toNumber(value);
            return [formatter ? formatter(numeric) : numeric, String(name)];
          }}
          labelFormatter={(label) => `${xLabel} ${label}`}
        />
        {series.length > 1 ? <Legend wrapperStyle={{ fontSize: 12 }} /> : null}
        {series.map((entry) => (
          <Line
            key={entry.key}
            type="monotone"
            dataKey={entry.key}
            name={entry.name}
            stroke={entry.color}
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}

interface GroupedBarChartProps {
  data: Array<Record<string, number | string>>;
  xKey: string;
  series: SeriesConfig[];
  xLabel: string;
  yLabel: string;
  formatter?: (value: number) => string;
  stacked?: boolean;
  domain?: [number, number];
}

/** Two or more measures side by side, e.g. cooperation versus defection. */
export function GroupedBarChart({
  data,
  xKey,
  series,
  xLabel,
  yLabel,
  formatter,
  stacked = false,
  domain,
}: GroupedBarChartProps) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data} margin={{ top: 8, right: 12, bottom: 28, left: 4 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={GRID_STROKE} vertical={false} />
        <XAxis
          dataKey={xKey}
          tick={AXIS_STYLE}
          interval={0}
          angle={-20}
          textAnchor="end"
          height={56}
          label={{ value: xLabel, position: "insideBottom", offset: -18, style: AXIS_STYLE }}
        />
        <YAxis
          tick={AXIS_STYLE}
          domain={domain}
          tickFormatter={formatter}
          label={{ value: yLabel, angle: -90, position: "insideLeft", style: AXIS_STYLE }}
        />
        <Tooltip
          contentStyle={TOOLTIP_STYLE}
          formatter={(value: unknown, name: unknown) => {
            const numeric = toNumber(value);
            return [formatter ? formatter(numeric) : numeric, String(name)];
          }}
        />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        {series.map((entry) => (
          <Bar
            key={entry.key}
            dataKey={entry.key}
            name={entry.name}
            fill={entry.color}
            stackId={stacked ? "stack" : undefined}
            radius={stacked ? undefined : [4, 4, 0, 0]}
          />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}

export interface SliceDatum {
  label: string;
  value: number;
  color: string;
}

/** Distribution of the four outcomes. */
export function OutcomePieChart({
  data,
  formatter,
}: {
  data: SliceDatum[];
  formatter?: (value: number) => string;
}) {
  const total = data.reduce((sum, slice) => sum + slice.value, 0);

  if (total === 0) {
    return (
      <div className="flex h-full items-center justify-center text-sm text-slate-500">
        No outcomes recorded yet.
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height="100%">
      <PieChart>
        <Pie
          data={data}
          dataKey="value"
          nameKey="label"
          innerRadius="45%"
          outerRadius="75%"
          paddingAngle={2}
        >
          {data.map((slice, index) => (
            <Cell key={index} fill={slice.color} />
          ))}
        </Pie>
        <Tooltip
          contentStyle={TOOLTIP_STYLE}
          formatter={(value: unknown, name: unknown) => {
            const numeric = toNumber(value);
            return [formatter ? formatter(numeric) : numeric, String(name)];
          }}
        />
        <Legend wrapperStyle={{ fontSize: 12 }} />
      </PieChart>
    </ResponsiveContainer>
  );
}
