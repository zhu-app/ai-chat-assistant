<script setup lang="ts">
import { computed } from 'vue';

export interface TelemetryData {
  firstTokenLatencyMs?: number;
  totalDurationMs?: number;
  tokensPerSecond?: number;
  inputTokens?: number;
  outputTokens?: number;
  estimatedCostUsd?: number;
  ragChunksRetrieved?: number;
  ragTopScore?: number;
  qualityScore?: number;
  qualityDetails?: {
    accuracy?: number;
    completeness?: number;
    clarity?: number;
    usefulness?: number;
    summary?: string;
  };
}

const props = defineProps<{
  telemetry: TelemetryData | null;
  visible: boolean;
}>();

const emit = defineEmits<{
  close: [];
}>();

const hasData = computed(() => props.telemetry !== null && props.telemetry !== undefined);

const scoreColor = (score: number | undefined) => {
  if (!score) return 'var(--text-muted)';
  if (score >= 8) return 'var(--success)';
  if (score >= 6) return 'var(--accent)';
  if (score >= 4) return '#f0a030';
  return 'var(--danger)';
};

const formatMs = (ms: number | undefined) => {
  if (!ms) return '-';
  if (ms < 1000) return `${Math.round(ms)}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
};

const formatCost = (usd: number | undefined) => {
  if (usd === undefined || usd === null) return '-';
  if (usd < 0.001) return `$${usd.toFixed(6)}`;
  if (usd < 0.01) return `$${usd.toFixed(4)}`;
  return `$${usd.toFixed(3)}`;
};
</script>

<template>
  <div v-if="visible && hasData" class="telemetry-panel">
    <div class="telemetry-panel__header">
      <span class="telemetry-panel__title">📊 响应分析</span>
      <button class="telemetry-panel__close" @click="emit('close')">✕</button>
    </div>

    <div class="telemetry-section">
      <div class="telemetry-section__title">⚡ 性能</div>
      <div class="telemetry-metrics">
        <div class="telemetry-metric">
          <span class="telemetry-metric__value">{{ formatMs(telemetry?.firstTokenLatencyMs) }}</span>
          <span class="telemetry-metric__label">首字延迟</span>
        </div>
        <div class="telemetry-metric">
          <span class="telemetry-metric__value">{{ formatMs(telemetry?.totalDurationMs) }}</span>
          <span class="telemetry-metric__label">总耗时</span>
        </div>
        <div class="telemetry-metric">
          <span class="telemetry-metric__value">{{ telemetry?.tokensPerSecond ?? '-' }}</span>
          <span class="telemetry-metric__label">tokens/s</span>
        </div>
      </div>
    </div>

    <div class="telemetry-section">
      <div class="telemetry-section__title">📝 Token 用量</div>
      <div class="telemetry-metrics">
        <div class="telemetry-metric">
          <span class="telemetry-metric__value">{{ telemetry?.inputTokens?.toLocaleString() ?? '-' }}</span>
          <span class="telemetry-metric__label">输入</span>
        </div>
        <div class="telemetry-metric">
          <span class="telemetry-metric__value">{{ telemetry?.outputTokens?.toLocaleString() ?? '-' }}</span>
          <span class="telemetry-metric__label">输出</span>
        </div>
        <div class="telemetry-metric">
          <span class="telemetry-metric__value">{{ formatCost(telemetry?.estimatedCostUsd) }}</span>
          <span class="telemetry-metric__label">估算成本</span>
        </div>
      </div>
    </div>

    <div v-if="(telemetry?.ragChunksRetrieved ?? 0) > 0" class="telemetry-section">
      <div class="telemetry-section__title">📚 知识库检索</div>
      <div class="telemetry-metrics">
        <div class="telemetry-metric">
          <span class="telemetry-metric__value">{{ telemetry?.ragChunksRetrieved }}</span>
          <span class="telemetry-metric__label">检索片段</span>
        </div>
        <div class="telemetry-metric">
          <span class="telemetry-metric__value">{{ telemetry?.ragTopScore?.toFixed(2) }}</span>
          <span class="telemetry-metric__label">最高相关度</span>
        </div>
      </div>
    </div>

    <div v-if="(telemetry?.qualityScore ?? 0) > 0" class="telemetry-section">
      <div class="telemetry-section__title">
        ⭐ 质量自评
        <span class="telemetry-quality-badge" :style="{ color: scoreColor(telemetry?.qualityScore) }">
          {{ telemetry?.qualityScore }}/10
        </span>
      </div>
      <div class="telemetry-quality-dims" v-if="telemetry?.qualityDetails">
        <div class="telemetry-quality-dim">
          <span class="telemetry-quality-dim__label">准确度</span>
          <div class="telemetry-quality-dim__bar">
            <div class="telemetry-quality-dim__fill" :style="{ width: `${(telemetry.qualityDetails.accuracy ?? 0) * 10}%`, background: scoreColor(telemetry.qualityDetails.accuracy) }" />
          </div>
          <span class="telemetry-quality-dim__value">{{ telemetry.qualityDetails.accuracy }}</span>
        </div>
        <div class="telemetry-quality-dim">
          <span class="telemetry-quality-dim__label">完整性</span>
          <div class="telemetry-quality-dim__bar">
            <div class="telemetry-quality-dim__fill" :style="{ width: `${(telemetry.qualityDetails.completeness ?? 0) * 10}%`, background: scoreColor(telemetry.qualityDetails.completeness) }" />
          </div>
          <span class="telemetry-quality-dim__value">{{ telemetry.qualityDetails.completeness }}</span>
        </div>
        <div class="telemetry-quality-dim">
          <span class="telemetry-quality-dim__label">清晰度</span>
          <div class="telemetry-quality-dim__bar">
            <div class="telemetry-quality-dim__fill" :style="{ width: `${(telemetry.qualityDetails.clarity ?? 0) * 10}%`, background: scoreColor(telemetry.qualityDetails.clarity) }" />
          </div>
          <span class="telemetry-quality-dim__value">{{ telemetry.qualityDetails.clarity }}</span>
        </div>
        <div class="telemetry-quality-dim">
          <span class="telemetry-quality-dim__label">实用性</span>
          <div class="telemetry-quality-dim__bar">
            <div class="telemetry-quality-dim__fill" :style="{ width: `${(telemetry.qualityDetails.usefulness ?? 0) * 10}%`, background: scoreColor(telemetry.qualityDetails.usefulness) }" />
          </div>
          <span class="telemetry-quality-dim__value">{{ telemetry.qualityDetails.usefulness }}</span>
        </div>
        <div v-if="telemetry.qualityDetails.summary" class="telemetry-quality-summary">
          {{ telemetry.qualityDetails.summary }}
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.telemetry-panel {
  position: fixed;
  bottom: 100px;
  right: 320px;
  width: 320px;
  max-height: 500px;
  overflow-y: auto;
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: 14px;
  box-shadow: var(--shadow-lg);
  z-index: 40;
  padding: 14px;
  display: grid;
  gap: 12px;
  animation: telemetryIn 0.3s ease-out;
}

@keyframes telemetryIn {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.telemetry-panel__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.telemetry-panel__title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.telemetry-panel__close {
  background: none;
  border: 0;
  font-size: 14px;
  color: var(--text-muted);
  cursor: pointer;
  padding: 2px 6px;
  border-radius: 4px;
}

.telemetry-panel__close:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.telemetry-section {
  display: grid;
  gap: 6px;
}

.telemetry-section__title {
  font-size: 11px;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  display: flex;
  align-items: center;
  gap: 6px;
}

.telemetry-metrics {
  display: flex;
  gap: 6px;
}

.telemetry-metric {
  flex: 1;
  background: var(--bg-card);
  border-radius: 8px;
  padding: 8px 6px;
  text-align: center;
  min-width: 0;
}

.telemetry-metric__value {
  display: block;
  font-size: 15px;
  font-weight: 700;
  color: var(--text-primary);
  font-variant-numeric: tabular-nums;
}

.telemetry-metric__label {
  display: block;
  font-size: 10px;
  color: var(--text-muted);
  margin-top: 2px;
}

.telemetry-quality-badge {
  font-size: 14px;
  font-weight: 700;
}

.telemetry-quality-dims {
  display: grid;
  gap: 4px;
}

.telemetry-quality-dim {
  display: flex;
  align-items: center;
  gap: 6px;
}

.telemetry-quality-dim__label {
  font-size: 11px;
  color: var(--text-secondary);
  width: 40px;
  flex-shrink: 0;
}

.telemetry-quality-dim__bar {
  flex: 1;
  height: 6px;
  background: var(--bg-tertiary);
  border-radius: 3px;
  overflow: hidden;
}

.telemetry-quality-dim__fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.5s ease;
}

.telemetry-quality-dim__value {
  font-size: 11px;
  font-weight: 600;
  color: var(--text-secondary);
  width: 20px;
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.telemetry-quality-summary {
  font-size: 11px;
  color: var(--text-muted);
  font-style: italic;
  margin-top: 4px;
  padding: 6px 8px;
  background: var(--bg-card);
  border-radius: 6px;
  line-height: 1.4;
}
</style>