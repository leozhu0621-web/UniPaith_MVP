import { useEffect, useRef, useState, ReactNode } from "react";

type AnimationVariant = "fade-up" | "fade-left" | "fade-right" | "scale-up" | "blur-in";

interface ScrollRevealProps {
  children: ReactNode;
  className?: string;
  delay?: number;
  variant?: AnimationVariant;
}

const variantStyles: Record<AnimationVariant, { hidden: string; visible: string }> = {
  "fade-up": {
    hidden: "opacity-0 translate-y-10",
    visible: "opacity-100 translate-y-0",
  },
  "fade-left": {
    hidden: "opacity-0 -translate-x-10",
    visible: "opacity-100 translate-x-0",
  },
  "fade-right": {
    hidden: "opacity-0 translate-x-10",
    visible: "opacity-100 translate-x-0",
  },
  "scale-up": {
    hidden: "opacity-0 scale-95",
    visible: "opacity-100 scale-100",
  },
  "blur-in": {
    hidden: "opacity-0 blur-sm scale-95",
    visible: "opacity-100 blur-0 scale-100",
  },
};

const ScrollReveal = ({ children, className = "", delay = 0, variant = "fade-up" }: ScrollRevealProps) => {
  const ref = useRef<HTMLDivElement>(null);
  const [isVisible, setIsVisible] = useState(false);
  const styles = variantStyles[variant];

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setTimeout(() => setIsVisible(true), delay);
          observer.unobserve(entry.target);
        }
      },
      { threshold: 0.1 }
    );

    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, [delay]);

  return (
    <div
      ref={ref}
      className={`transition-all duration-800 ease-out ${
        isVisible ? styles.visible : styles.hidden
      } ${className}`}
      style={{ transitionDuration: "800ms" }}
    >
      {children}
    </div>
  );
};

export default ScrollReveal;
