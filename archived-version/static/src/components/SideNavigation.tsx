// Layer 01 — left vertical navigation. Only Overview is functional this phase.

import type { ComponentType } from 'react';
import {
  IconDoc,
  IconFlow,
  IconCoin,
  IconOverview,
  IconShield,
  IconStack,
  IconTrend,
} from './icons';

interface NavItem {
  id: string;
  label: string;
  icon: ComponentType<{ size?: number; className?: string }>;
  active?: boolean;
  disabled?: boolean;
}

const ITEMS: NavItem[] = [
  { id: 'overview', label: 'Overview', icon: IconOverview, active: true },
  { id: 'performance', label: 'Performance', icon: IconTrend, disabled: true },
  { id: 'risk', label: 'Risk', icon: IconShield, disabled: true },
  { id: 'operations', label: 'Operations', icon: IconFlow, disabled: true },
  { id: 'value', label: 'Value', icon: IconCoin, disabled: true },
  { id: 'batches', label: 'Batches', icon: IconStack, disabled: true },
  { id: 'reports', label: 'Reports', icon: IconDoc, disabled: true },
];

export function SideNavigation() {
  return (
    <nav className="nav" aria-label="Primary">
      <div className="nav__brand">
        <span className="nav__brand-mark" aria-hidden="true">
          CT
        </span>
        <div className="nav__brand-text">
          <span className="nav__brand-name">Circular Timber</span>
          <span className="nav__brand-sub">Intelligence</span>
        </div>
      </div>

      <ul className="nav__list">
        {ITEMS.map((item) => {
          const Icon = item.icon;
          return (
            <li key={item.id}>
              <button
                type="button"
                className="nav__item"
                aria-current={item.active ? 'page' : undefined}
                disabled={item.disabled}
                title={item.disabled ? 'Not implemented in this phase' : item.label}
              >
                <Icon size={17} className="nav__icon" />
                <span>{item.label}</span>
                {item.disabled && <span className="nav__soon" aria-hidden="true" />}
              </button>
            </li>
          );
        })}
      </ul>

      <div className="nav__foot">
        <span className="nav__chip">Synthetic Prototype</span>
        <p className="nav__note">Seed 20260818 · 2025 dataset</p>
      </div>
    </nav>
  );
}
