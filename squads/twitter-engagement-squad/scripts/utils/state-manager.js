const fs = require('fs');
const path = require('path');

const STATE_PATH = path.join(__dirname, '../../state.json');

function updateState(updates) {
  try {
    const raw = fs.readFileSync(STATE_PATH, 'utf-8');
    const state = JSON.parse(raw);
    
    const newState = {
      ...state,
      ...updates,
      updatedAt: new Date().toISOString()
    };
    
    fs.writeFileSync(STATE_PATH, JSON.stringify(newState, null, 2), 'utf-8');
    return newState;
  } catch (e) {
    console.error('❌ Error updating state.json:', e.message);
    return null;
  }
}

function setStep(number, label, status = 'running', error = null) {
  return updateState({
    status: error ? 'error' : status,
    errorMessage: error,
    step: {
      current: number,
      total: 5,
      label: label
    }
  });
}

function setAgentStatus(agentId, status) {
  const raw = fs.readFileSync(STATE_PATH, 'utf-8');
  const state = JSON.parse(raw);
  
  const agents = state.agents.map(a => {
    if (a.id === agentId) return { ...a, status };
    return a;
  });
  
  return updateState({ agents });
}

module.exports = {
  updateState,
  setStep,
  setAgentStatus
};
