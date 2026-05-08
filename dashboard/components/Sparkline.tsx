export function Sparkline({
  values,
  width = 140,
  height = 40,
  positive = true,
}: {
  values: number[];
  width?: number;
  height?: number;
  positive?: boolean;
}) {
  if (!values?.length) return null;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const step = width / (values.length - 1);

  const points = values
    .map((v, i) => `${i * step},${height - ((v - min) / range) * height}`)
    .join(" ");

  const stroke = positive ? "#5fa67a" : "#c45050";
  const fill = positive ? "rgba(95,166,122,0.12)" : "rgba(196,80,80,0.12)";

  return (
    <svg width={width} height={height} className="overflow-visible">
      <defs>
        <linearGradient id={`grad-${stroke}`} x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stopColor={stroke} stopOpacity="0.35" />
          <stop offset="100%" stopColor={stroke} stopOpacity="0" />
        </linearGradient>
      </defs>
      <polygon
        points={`0,${height} ${points} ${width},${height}`}
        fill={fill}
      />
      <polyline
        points={points}
        fill="none"
        stroke={stroke}
        strokeWidth="1.4"
        strokeLinejoin="round"
        strokeLinecap="round"
      />
      <circle
        cx={width}
        cy={height - ((values[values.length - 1] - min) / range) * height}
        r="2.2"
        fill={stroke}
      />
    </svg>
  );
}
