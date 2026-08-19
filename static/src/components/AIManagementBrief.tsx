// Layer 02 — AI Management Brief. Renders the structured payload served by the
// mock data layer (management_brief.json). No business logic here — the numbers
// and headlines originate from the approved synthetic dataset. Clicking an item
// opens Ask Circular with the relevant question pre-loaded.

import type { ManagementBriefItem } from '../data/dashboardData';
import { IconArrowRight, IconSpark } from './icons';

export function AIManagementBrief({
  items,
  onAsk,
}: {
  items: ManagementBriefItem[];
  onAsk: (questionId: string) => void;
}) {
  return (
    <section className="brief" aria-labelledby="brief-title">
      <div className="brief__greeting">
        <span className="brief__greeting-mark" aria-hidden="true">
          <IconSpark size={15} />
        </span>
        <span>Good morning, Olivia</span>
      </div>
      <h2 id="brief-title" className="brief__title">
        3 things need your attention today
      </h2>
      <ul className="brief__list">
        {items.map((item, i) => (
          <li key={item.id}>
            <button
              type="button"
              className="brief__item"
              data-severity={item.severity}
              onClick={() => onAsk(item.question_id ?? items[0]?.question_id ?? 'q1')}
              aria-label={`${item.title} ${item.detail}`}
            >
              <span className="brief__index" aria-hidden="true">
                {String(i + 1).padStart(2, '0')}
              </span>
              <span className="brief__body">
                <span className="brief__headline">{item.title}</span>
                <span className="brief__detail">{item.detail}</span>
              </span>
              <span className="brief__arrow" aria-hidden="true">
                <IconArrowRight size={15} />
              </span>
            </button>
          </li>
        ))}
      </ul>
      <button type="button" className="btn btn--ask" onClick={() => onAsk(items[0]?.question_id ?? 'q1')}>
        Ask Circular
        <IconSpark size={15} />
      </button>
    </section>
  );
}
