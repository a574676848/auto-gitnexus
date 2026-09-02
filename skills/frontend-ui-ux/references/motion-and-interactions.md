# 高阶动效编排与微交互指南 (Motion & Interactions)

## 1. 动效设计原则与性能守卫

1. **动效必须服务于意图 (Motivated Motion)**：每一次位移与淡入必须服务于层级展示 (Hierarchy)、叙事推进 (Storytelling) 或状态反馈 (Feedback)。严禁为了炫技无节制堆砌动效。
2. **硬件加速白名单**：动画严格仅操作 `transform` 与 `opacity`。严禁直接对 `top`、`left`、`width`、`height` 产生动画补间。
3. **滚动监听硬禁令**：**严禁使用 `window.addEventListener('scroll')`**，必须使用 Motion 的 `useScroll` 或 GSAP 的 `ScrollTrigger`。
4. **无障碍降级保护**：当检测到系统开启 `prefers-reduced-motion` 时，所有滚动吸顶、画卷展开与磁吸微动效必须安全降级为常规静态布局。

---

## 2. GSAP 高阶核心范式与代码骨架

### 2.1 滚动卡片吸顶堆叠 (Sticky-Stack Canonical)
卡片在滚动至视口顶部时固定并随着下一张卡片的推入产生等比缩放与淡出：

```tsx
"use client";
import { useRef, useEffect } from "react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { useReducedMotion } from "motion/react";

gsap.registerPlugin(ScrollTrigger);

export function StickyStack({ cards }: { cards: React.ReactNode[] }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const shouldReduceMotion = useReducedMotion();

  useEffect(() => {
    if (shouldReduceMotion || !containerRef.current) return;
    const ctx = gsap.context(() => {
      const cardElements = gsap.utils.toArray<HTMLElement>(".stack-card");
      cardElements.forEach((card, index) => {
        if (index === cardElements.length - 1) return;
        ScrollTrigger.create({
          trigger: card,
          start: "top top",
          endTrigger: cardElements[cardElements.length - 1],
          end: "top top",
          pin: true,
          pinSpacing: false,
        });
        gsap.to(card, {
          scale: 0.92,
          opacity: 0.5,
          ease: "none",
          scrollTrigger: {
            trigger: cardElements[index + 1],
            start: "top bottom",
            end: "top top",
            scrub: true,
          },
        });
      });
    }, containerRef);
    return () => ctx.revert();
  }, [shouldReduceMotion]);

  return (
    <div ref={containerRef} className="relative">
      {cards.map((card, idx) => (
        <div key={idx} className="stack-card sticky top-0 min-h-[100dvh] flex items-center justify-center">
          {card}
        </div>
      ))}
    </div>
  );
}
```

### 2.2 垂直滚动转横向画卷 (Horizontal-Pan Canonical)
```tsx
"use client";
import { useRef, useEffect } from "react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { useReducedMotion } from "motion/react";

gsap.registerPlugin(ScrollTrigger);

export function HorizontalPan({ children }: { children: React.ReactNode }) {
  const sectionRef = useRef<HTMLDivElement>(null);
  const trackRef = useRef<HTMLDivElement>(null);
  const shouldReduceMotion = useReducedMotion();

  useEffect(() => {
    if (shouldReduceMotion || !sectionRef.current || !trackRef.current) return;
    const ctx = gsap.context(() => {
      const totalScroll = trackRef.current!.scrollWidth - window.innerWidth;
      gsap.to(trackRef.current, {
        x: -totalScroll,
        ease: "none",
        scrollTrigger: {
          trigger: sectionRef.current,
          start: "top top",
          end: () => `+=${totalScroll}`,
          pin: true,
          scrub: 1,
          invalidateOnRefresh: true,
        },
      });
    }, sectionRef);
    return () => ctx.revert();
  }, [shouldReduceMotion]);

  return (
    <section ref={sectionRef} className="relative overflow-hidden">
      <div ref={trackRef} className="flex h-[100dvh] items-center">
        {children}
      </div>
    </section>
  );
}
```

---

## 3. Motion 物理微动效范式

### 3.1 视口入场级联 (Reveal Stagger)
无需复杂 ScrollTrigger，适用于列表、网格与特性介绍：
```tsx
"use client";
import { motion, useReducedMotion } from "motion/react";

export function RevealStagger({ items }: { items: { id: string; content: React.ReactNode }[] }) {
  const shouldReduceMotion = useReducedMotion();

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
      {items.map((item, index) => (
        <motion.div
          key={item.id}
          initial={shouldReduceMotion ? false : { opacity: 0, y: 24 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.2 }}
          transition={{
            duration: 0.7,
            delay: index * 0.08,
            ease: [0.16, 1, 0.3, 1], // 自定义弹性曲线
          }}
        >
          {item.content}
        </motion.div>
      ))}
    </div>
  );
}
```

### 3.2 阻尼弹簧微物理规范 (Spring Physics Spec)
所有微交互（按键、卡片浮动、Tab 切换）统一采用弹簧阻尼模型：
```ts
export const SPRING_PHYSICS = {
  tactile: { type: "spring", stiffness: 400, damping: 30 },
  gentle: { type: "spring", stiffness: 120, damping: 20 },
  bouncy: { type: "spring", stiffness: 200, damping: 15 },
};
```
