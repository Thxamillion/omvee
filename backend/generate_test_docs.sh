#!/bin/bash
# Generate beautiful HTML test documentation

echo "🧪 Generating test documentation..."

# Activate virtual environment
source venv/bin/activate

# Run tests with HTML report and coverage
python -m pytest tests/ \
    --html=test_report.html \
    --self-contained-html \
    --cov=app \
    --cov-report=html \
    --cov-report=term-missing \
    -v

echo ""
echo "✅ Test documentation generated!"
echo ""
echo "📊 Open these files in your browser:"
echo "   • Test Report:    file://$(pwd)/test_report.html"
echo "   • Coverage Report: file://$(pwd)/htmlcov/index.html"
echo ""
echo "🚀 Or run:"
echo "   open test_report.html"
echo "   open htmlcov/index.html"