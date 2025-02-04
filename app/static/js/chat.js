// chat.js

/**
 * Chat Interface Module
 * Handles all client-side functionality for the chat interface including:
 * - Message management
 * - Form submissions
 * - Data visualization
 * - Analysis features
 */

class ChatInterface {
    constructor() {
        // DOM Elements
        this.elements = {
            queryForm: document.getElementById('queryForm'),
            queryInput: document.getElementById('queryInput'),
            messagesContainer: document.getElementById('messages'),
            typingIndicator: document.getElementById('typingIndicator'),
            visualizationContainer: document.getElementById('visualization-container'),
            analysisContent: document.getElementById('analysis-content'),
            chartContent: document.getElementById('chart-content'),
            submitButton: document.querySelector('button[type="submit"]'),
            visualizeButton: document.getElementById('visualizeBtn'),
            analyzeButton: document.getElementById('analyzeBtn')
        };

        // State management
        this.state = {
            currentChart: null,
            messagesArray: []
        };

        // Initialize the interface
        this.initialize();
    }

    /**
     * Initialize all event listeners and setup
     */
    initialize() {
        // Form submission handler
        this.elements.queryForm.addEventListener('submit', (e) => this.handleFormSubmit(e));

        // Button click handlers
        this.elements.visualizeButton.addEventListener('click', () => this.requestVisualization());
        this.elements.analyzeButton.addEventListener('click', () => this.requestAnalysis());

        // Input validation
        this.elements.queryInput.addEventListener('input', () => this.validateInput());
    }

    /**
     * Add a message to the chat interface
     * @param {string} content - The message content
     * @param {boolean} isUser - Whether the message is from the user
     */
    addMessage(content, isUser = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = isUser 
            ? 'user-message p-4 max-w-3/4 text-gray-700'
            : 'assistant-message p-4 max-w-3/4 text-gray-700';
        messageDiv.textContent = content;
        
        this.elements.messagesContainer.appendChild(messageDiv);
        messageDiv.scrollIntoView({ behavior: 'smooth' });
        this.state.messagesArray.push({ content, isUser });
    }

    /**
     * Toggle the typing indicator
     * @param {boolean} visible - Whether to show the typing indicator
     */
    setTypingIndicator(visible) {
        this.elements.typingIndicator.className = visible ? 'px-6 py-2' : 'hidden px-6 py-2';
    }

    /**
     * Handle form submission and send query to server
     * @param {Event} e - Form submission event
     */
    async handleFormSubmit(e) {
        e.preventDefault();
        
        const query = this.elements.queryInput.value.trim();
        if (!query) return;

        this.addMessage(query, true);
        this.elements.queryInput.value = '';
        this.setTypingIndicator(true);

        try {
            const response = await fetch('/api/query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query })
            });

            const data = await response.json();
            this.setTypingIndicator(false);

            if (response.ok) {
                this.addMessage(JSON.stringify(data, null, 2));
            } else {
                this.addMessage(`Error: ${data.error}`);
            }
        } catch (error) {
            this.setTypingIndicator(false);
            this.addMessage('Error: Could not connect to server');
        }
    }

    /**
     * Display analysis results in the interface
     * @param {Object} analysis - Analysis data from the server
     */
    displayAnalysis(analysis) {
        this.elements.analysisContent.innerHTML = '';
        const container = document.createElement('div');
        container.className = 'bg-white rounded-lg shadow p-4 mb-4';

        // Dataset overview section
        container.innerHTML += this.generateDatasetOverview(analysis);

        // Column analysis section
        if (analysis.columns) {
            container.innerHTML += this.generateColumnAnalysis(analysis.columns);
        }

        // Summary statistics section
        if (analysis.summary_stats && Object.keys(analysis.summary_stats).length > 0) {
            container.innerHTML += this.generateSummaryStatistics(analysis.summary_stats);
        }

        this.elements.analysisContent.appendChild(container);
        this.elements.visualizationContainer.classList.remove('hidden');
    }

    /**
     * Generate HTML for dataset overview section
     * @param {Object} analysis - Analysis data
     * @returns {string} HTML string
     */
    generateDatasetOverview(analysis) {
        return `
            <div class="mb-4">
                <h3 class="text-lg font-semibold mb-2">Dataset Overview</h3>
                <p>Total Records: ${analysis.record_count}</p>
            </div>
        `;
    }

    /**
     * Generate HTML for column analysis section
     * @param {Object} columns - Column analysis data
     * @returns {string} HTML string
     */
    generateColumnAnalysis(columns) {
        return `
            <div class="mb-4">
                <h3 class="text-lg font-semibold mb-2">Column Analysis</h3>
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    ${Object.entries(columns).map(([col, info]) => `
                        <div class="bg-gray-50 p-3 rounded">
                            <h4 class="font-medium mb-2">${col}</h4>
                            <ul class="text-sm">
                                <li>Type: ${info.type}</li>
                                <li>Unique Values: ${info.unique_values}</li>
                                <li>Null Count: ${info.null_count}</li>
                            </ul>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    /**
     * Generate HTML for summary statistics section
     * @param {Object} stats - Summary statistics data
     * @returns {string} HTML string
     */
    generateSummaryStatistics(stats) {
        return `
            <div class="mb-4">
                <h3 class="text-lg font-semibold mb-2">Summary Statistics</h3>
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    ${Object.entries(stats).map(([col, stat]) => `
                        <div class="bg-gray-50 p-3 rounded">
                            <h4 class="font-medium mb-2">${col}</h4>
                            <ul class="text-sm">
                                <li>Min: ${stat.min.toFixed(2)}</li>
                                <li>Max: ${stat.max.toFixed(2)}</li>
                                <li>Mean: ${stat.mean.toFixed(2)}</li>
                                <li>Median: ${stat.median.toFixed(2)}</li>
                            </ul>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    /**
     * Update or create a new chart
     * @param {Object} vizData - Visualization data from the server
     */
    updateChart(vizData) {
        // Cleanup existing chart
        if (this.state.currentChart) {
            this.state.currentChart.destroy();
        }

        this.elements.chartContent.innerHTML = '';
        const canvas = document.createElement('canvas');
        this.elements.chartContent.appendChild(canvas);

        // Create new chart instance
        this.state.currentChart = new Chart(canvas, {
            type: vizData.type,
            data: {
                labels: vizData.labels,
                datasets: vizData.datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Data Visualization'
                    }
                }
            }
        });

        this.elements.visualizationContainer.classList.remove('hidden');
    }

    /**
     * Request visualization from the server
     */
    async requestVisualization() {
        const lastResponse = this.state.messagesArray.filter(msg => !msg.isUser).pop();
        
        if (!lastResponse) {
            console.error('No data available for visualization');
            return;
        }

        this.setTypingIndicator(true);
        
        try {
            // Get data analysis
            const analysisResponse = await fetch('/api/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    data: JSON.parse(lastResponse.content)
                })
            });

            const analysisData = await analysisResponse.json();
            
            if (analysisData.error) {
                throw new Error(analysisData.error);
            }

            // Request visualization with default type
            const vizResponse = await fetch('/api/visualize', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    data: JSON.parse(lastResponse.content),
                    visualization_type: 'bar'
                })
            });

            const vizData = await vizResponse.json();
            
            if (vizData.error) {
                throw new Error(vizData.error);
            }

            this.setTypingIndicator(false);
            this.updateChart(vizData);
            
        } catch (error) {
            this.handleVisualizationError(error);
        }
    }

    /**
     * Request data analysis from the server
     */
    async requestAnalysis() {
        const lastResponse = this.state.messagesArray.filter(msg => !msg.isUser).pop();
        
        if (!lastResponse) {
            console.error('No data available for analysis');
            return;
        }

        try {
            const response = await fetch('/api/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    data: JSON.parse(lastResponse.content)
                })
            });

            const analysisData = await response.json();
            
            if (analysisData.error) {
                throw new Error(analysisData.error);
            }

            this.displayAnalysis(analysisData);
            
        } catch (error) {
            this.handleAnalysisError(error);
        }
    }

    /**
     * Handle visualization errors
     * @param {Error} error - Error object
     */
    handleVisualizationError(error) {
        console.error('Error creating visualization:', error);
        this.showError(`Error creating visualization: ${error.message}`);
        this.setTypingIndicator(false);
    }

    /**
     * Handle analysis errors
     * @param {Error} error - Error object
     */
    handleAnalysisError(error) {
        console.error('Error performing analysis:', error);
        this.showError(`Error performing analysis: ${error.message}`);
    }

    /**
     * Display error message in the visualization container
     * @param {string} message - Error message to display
     */
    showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'bg-red-100 border-l-4 border-red-500 text-red-700 p-4 mb-4';
        errorDiv.textContent = message;
        this.elements.visualizationContainer.insertBefore(
            errorDiv,
            this.elements.visualizationContainer.firstChild
        );
    }

    /**
     * Validate input and update submit button state
     */
    validateInput() {
        const hasValue = this.elements.queryInput.value.trim() !== '';
        this.elements.submitButton.disabled = !hasValue;
        this.elements.submitButton.className = hasValue
            ? 'bg-tertiary text-white px-6 py-2 rounded-lg hover:opacity-50 focus:outline-none focus:ring-2 focus:ring-blue-500'
            : 'bg-gray-400 text-white px-6 py-2 rounded-lg cursor-not-allowed';
    }
}

// Initialize the chat interface when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ChatInterface();
});