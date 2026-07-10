import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, request, jsonify
from core.collector import CollectorManager
from core.analyzer import ProductAnalyzer
from utils.visualizer import Visualizer

app = Flask(__name__, template_folder='templates', static_folder='static')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/search', methods=['POST'])
def search():
    data = request.json
    keyword = data.get('keyword', '').strip()
    platforms = data.get('platforms', ['京东', '淘宝', '拼多多'])
    max_results = data.get('max_results', 15)
    use_mock = data.get('use_mock', True)

    if not keyword:
        return jsonify({'error': '请输入搜索关键词'}), 400

    try:
        manager = CollectorManager(use_mock=use_mock, platforms=platforms)
        analyzer = ProductAnalyzer()
        visualizer = Visualizer()

        products = manager.search_all(keyword, max_results_per_platform=max_results)
        result = analyzer.analyze(keyword, products)
        charts = visualizer.generate_all_charts(result)

        return jsonify({
            'success': True,
            'result': result.to_dict(),
            'charts': charts
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/demo')
def demo():
    demo_file = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                             'examples', 'demo_result.json')
    if os.path.exists(demo_file):
        import json
        with open(demo_file, 'r', encoding='utf-8') as f:
            result = json.load(f)
        return jsonify({'success': True, 'result': result})
    return jsonify({'error': '演示数据不存在'}), 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
