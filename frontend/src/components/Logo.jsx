export default function Logo({ size = 28 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" fill="none" aria-hidden="true">
      <rect width="32" height="32" rx="8" fill="#0F6B5C" />
      <circle cx="11" cy="20" r="3" fill="#FFFFFF" />
      <circle cx="16" cy="12" r="3" fill="#FFFFFF" />
      <circle cx="22" cy="17" r="3" fill="#C98A2B" />
      <path d="M11 20 L16 12 L22 17" stroke="#FFFFFF" strokeWidth="1.4" strokeLinecap="round" opacity="0.55" />
    </svg>
  )
}
