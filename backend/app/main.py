"""
IraqQuant Platform - Main Application
Software-based Quantum Computing Platform
"""
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import os

from .config import Config
from .api import auth_bp, jobs_bp


def create_app():
    """Create and configure Flask application"""
    
    app = Flask(__name__,
                static_folder='../../frontend',
                static_url_path='')
    
    # Configuration
    app.config.from_object(Config)
    
    # Enable CORS for all routes
    CORS(app, resources={
        r"/api/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(jobs_bp)
    
    # Health check endpoint
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """System health check"""
        return jsonify({
            'status': 'healthy',
            'platform': Config.PLATFORM_NAME,
            'version': Config.VERSION,
            'description': Config.DESCRIPTION
        }), 200
    
    # Platform info endpoint
    @app.route('/api/info', methods=['GET'])
    def platform_info():
        """Platform information and capabilities"""
        return jsonify({
            'platform': Config.PLATFORM_NAME,
            'version': Config.VERSION,
            'description': Config.DESCRIPTION,
            'capabilities': {
                'max_qubits': Config.MAX_QUBITS,
                'min_qubits': Config.MIN_QUBITS,
                'max_shots': Config.MAX_SHOTS,
                'max_depth': Config.MAX_DEPTH,
                'backends': ['mps', 'photonic'],
                'features': [
                    'Realistic Noise Models',
                    'Quantum Error Correction',
                    'Multi-Backend Support',
                    'Burst Event Processing',
                    'Surface Code QEC'
                ]
            },
            'noise_models': {
                'pauli': {
                    'default_error_rate': Config.DEFAULT_ERROR_RATE,
                    'readout_error': Config.READOUT_ERROR
                },
                'decoherence': {
                    't1_us': Config.T1_TIME_US,
                    't2_us': Config.T2_TIME_US,
                    'single_qubit_gate_ns': Config.SINGLE_QUBIT_GATE_TIME_NS,
                    'two_qubit_gate_ns': Config.TWO_QUBIT_GATE_TIME_NS
                },
                'burst_events': {
                    'rate_per_hour': Config.BURST_RATE_PER_HOUR,
                    'min_qubits': Config.MIN_BURST_QUBITS,
                    'max_qubits': Config.MAX_BURST_QUBITS
                }
            },
            'topologies': Config.TOPOLOGY_LEVELS
        }), 200
    
    # Serve frontend
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_frontend(path):
        """Serve static frontend files"""
        if path and os.path.exists(os.path.join(app.static_folder, path)):
            return send_from_directory(app.static_folder, path)
        else:
            return send_from_directory(app.static_folder, 'index.html')
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500
    
    return app


# Create app instance
app = create_app()


if __name__ == '__main__':
    # Run development server
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
