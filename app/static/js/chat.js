// app/static/js/chat.js
class MCPChat {
    constructor() {
        this.messageQueue = [];
        this.isProcessing = false;
        this.initialize();
    }

    initialize() {
        // Initialize chart instance if visualization is needed
        this.chart = null;
        
        // Setup WebSocket connection if needed
        this.setupWebSocket();
        
        // Initialize event listeners
        this.setupEventListeners();
    }

    setupWebSocket() {
        // Optional: Setup WebSocket for real-time updates
        // this.ws = new WebSocket('ws://' + window.location.host + '/ws');
        // this.ws.onmessage = this.handleWebSocketMessage.bind(this);
    }

    setupEventListeners() {
        // Message history handler
        document.getElementById('historyBtn')?.addEventListener('click', () => {
            this.loadMessageHistory();
        });
    }

    async sendQuery(query) {
        try {
            const response = await fetch('/api/query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ query })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            console.log('Query response:', data);
            return data;

        } catch (error) {
            console.error('Error sending query:', error);
            throw error;
        }
    }

    displayVisualization(data) {
        // Implementation depends on your visualization library
        // Example using Chart.js
        const ctx = document.getElementById('visualizationCanvas');
        if (this.chart) {
            this.chart.destroy();
        }
        
        this.chart = new Chart(ctx, {
            type: data.type || 'bar',
            data: data.chartData,
            options: data.options
        });
    }

    async loadMessageHistory() {
        try {
            const response = await fetch('/api/history');
            const history = await response.json();
            this.displayMessageHistory(history);
        } catch (error) {
            console.error('Error loading message history:', error);
        }
    }

    displayMessageHistory(history) {
        const historyContainer = document.getElementById('messageHistory');
        historyContainer.innerHTML = '';
        
        history.forEach(message => {
            const messageElement = document.createElement('div');
            messageElement.className = `message ${message.type}`;
            messageElement.textContent = message.content;
            historyContainer.appendChild(messageElement);
        });
    }

    // Utility methods
    formatResponse(response) {
        if (typeof response === 'object') {
            return JSON.stringify(response, null, 2);
        }
        return response;
    }

    showError(message) {
        const errorContainer = document.getElementById('errorContainer');
        errorContainer.textContent = message;
        errorContainer.style.display = 'block';
        setTimeout(() => {
            errorContainer.style.display = 'none';
        }, 5000);
    }
}

// Initialize chat when document is ready
document.addEventListener('DOMContentLoaded', () => {
    window.mcpChat = new MCPChat();
});