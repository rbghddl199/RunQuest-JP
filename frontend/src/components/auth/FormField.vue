<script setup>
defineProps({
  id: {
    type: String,
    required: true,
  },
  label: {
    type: String,
    required: true,
  },
  modelValue: {
    type: String,
    default: '',
  },
  type: {
    type: String,
    default: 'text',
  },
  placeholder: {
    type: String,
    default: '',
  },
  autocomplete: {
    type: String,
    default: 'off',
  },
  error: {
    type: String,
    default: '',
  },
  help: {
    type: String,
    default: '',
  },
})

defineEmits(['update:modelValue'])
</script>

<template>
  <div class="form-field">
    <label :for="id">{{ label }}</label>
    <div class="form-field__control" :class="{ 'form-field__control--error': error }">
      <span v-if="$slots.icon" class="form-field__icon"><slot name="icon" /></span>
      <input
        :id="id"
        :value="modelValue"
        :type="type"
        :placeholder="placeholder"
        :autocomplete="autocomplete"
        :aria-invalid="Boolean(error)"
        :aria-describedby="error || help ? `${id}-message` : undefined"
        @input="$emit('update:modelValue', $event.target.value)"
      />
      <span v-if="$slots.action" class="form-field__action"><slot name="action" /></span>
    </div>
    <p v-if="error || help" :id="`${id}-message`" :class="{ 'is-error': error }">
      {{ error || help }}
    </p>
  </div>
</template>

<style scoped>
.form-field {
  display: grid;
  gap: 6px;
}

.form-field label {
  color: var(--color-navy);
  font-size: 13px;
  font-weight: 800;
}

.form-field__control {
  display: grid;
  min-height: 48px;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: 10px;
  padding: 0 13px;
  background: #fff;
  border: 1px solid var(--color-border);
  border-radius: 14px;
  transition: border-color 160ms ease, box-shadow 160ms ease;
}

.form-field__control:focus-within {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(8, 102, 255, 0.1);
}

.form-field__control--error {
  border-color: #df4f5f;
}

.form-field__icon {
  display: grid;
  color: #8795aa;
  place-items: center;
}

.form-field input {
  width: 100%;
  min-width: 0;
  padding: 12px 0;
  color: var(--color-navy);
  background: transparent;
  border: 0;
  outline: 0;
}

.form-field input::placeholder {
  color: #a4afbf;
}

.form-field__action {
  display: flex;
  align-items: center;
}

.form-field p {
  margin: -1px 0 0;
  color: var(--color-muted);
  font-size: 10px;
  line-height: 1.45;
}

.form-field p.is-error {
  color: #d73c4e;
}
</style>
