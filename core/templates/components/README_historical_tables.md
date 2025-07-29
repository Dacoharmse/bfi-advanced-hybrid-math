# Historical Tables Component

A professional, reusable Jinja2 template component for displaying historical market data and other tabular information with the BFI Signals golden theme styling.

## Overview

The Historical Tables Component provides a flexible, responsive table solution that seamlessly integrates with the BFI Signals application's golden theme while offering a clean minimal alternative. It's designed specifically for financial data but works with any tabular data.

## Features

### Core Functionality
- **Dual Theme Support**: Golden (luxury) and Minimal (clean) styling options
- **Responsive Design**: Mobile-first approach with tablet and desktop optimizations
- **Interactive Elements**: Click-to-copy values, sortable columns, hover animations
- **Data Flexibility**: Supports both array and dictionary data structures
- **Export Capabilities**: Built-in CSV export with data cleaning
- **Pagination Support**: Server-side pagination with navigation controls
- **Professional Empty States**: Elegant no-data displays with custom messages

### Advanced Features
- **Color-coded Changes**: Automatic positive/negative value highlighting
- **Customizable Actions**: Configurable action buttons with callback functions
- **Copy Functionality**: Modern clipboard API with fallback support
- **Loading States**: Shimmer animations for data loading
- **Accessibility**: ARIA labels and keyboard navigation support
- **Performance Optimized**: Minimal DOM manipulation and efficient rendering

## Installation

The component is located at:
```
/core/templates/components/historical_tables.html
```

Simply include it in your Jinja2 templates to use.

## Basic Usage

### Simple Table
```jinja2
{% set table_data = [
    ['2025-01-20', '21,450.25', '+125.50'],
    ['2025-01-19', '21,324.75', '-45.25']
] %}
{% set table_headers = ['Date', 'Value', 'Change'] %}
{% set table_title = 'Market Data' %}
{% include 'components/historical_tables.html' %}
```

### Dictionary Data
```jinja2
{% set table_data = [
    {
        'date': '2025-01-20',
        'value': '21,450.25',
        'change': '+125.50'
    }
] %}
{% set table_headers = ['Date', 'Value', 'Change'] %}
{% set table_title = 'Market Data' %}
{% include 'components/historical_tables.html' %}
```

## Configuration Parameters

### Required Parameters
- `table_data`: List of dictionaries or arrays containing row data
- `table_headers`: List of column header strings

### Optional Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `table_title` | String | None | Title displayed in table header |
| `table_id` | String | 'historical-table' | Unique identifier for the table |
| `table_style` | String | 'golden' | Theme: 'golden' or 'minimal' |
| `show_pagination` | Boolean | False | Enable pagination controls |
| `pagination_info` | Object | None | Pagination data object |
| `show_export` | Boolean | True | Show export button |
| `show_actions` | Boolean | True | Show actions column |
| `icon_src` | String | None | Path to icon for table title |
| `empty_message` | String | 'No historical data available' | Custom empty state message |
| `sortable_columns` | List | [] | Column indices that are sortable |
| `value_columns` | List | [] | Column indices with copyable values |
| `change_columns` | List | [] | Column indices showing +/- changes |

## Theme Options

### Golden Theme (`table_style = 'golden'`)
- Luxury golden gradient headers
- Warm hover effects with golden highlighting
- Professional shadows and borders
- Perfect for main dashboard displays

### Minimal Theme (`table_style = 'minimal'`)
- Clean, modern appearance
- Subtle animations and interactions
- Optimized for secondary data displays
- Better for dense information layouts

## Advanced Configuration

### Market Data Example
```jinja2
{% set table_data = nasdaq_historical_data %}
{% set table_headers = ['Date', 'Current', 'Change', 'Previous', 'High', 'Low'] %}
{% set table_title = 'NASDAQ Historical Data' %}
{% set table_id = 'nasdaq-history' %}
{% set table_style = 'golden' %}
{% set icon_src = url_for('static', filename='nasdaq.svg') %}
{% set sortable_columns = [0, 1, 2, 3, 4, 5] %}
{% set value_columns = [1, 3, 4, 5] %}
{% set change_columns = [2] %}
{% set show_pagination = true %}
{% set pagination_info = pagination_data %}
{% include 'components/historical_tables.html' %}
```

### Trading Signals Example
```jinja2
{% set table_data = trading_signals %}
{% set table_headers = ['Time', 'Signal', 'Pair', 'Entry', 'Target', 'Stop', 'Status'] %}
{% set table_title = 'Trading Signals History' %}
{% set table_style = 'minimal' %}
{% set sortable_columns = [0, 1, 2] %}
{% set value_columns = [3, 4, 5] %}
{% set show_actions = false %}
{% include 'components/historical_tables.html' %}
```

## Pagination Object Structure

When using pagination, provide a `pagination_info` object with this structure:
```python
pagination_info = {
    'current_page': 1,
    'total_pages': 5,
    'start_item': 1,
    'end_item': 20,
    'total_items': 95,
    'has_prev': False,
    'has_next': True,
    'prev_page': None,
    'next_page': 2
}
```

## JavaScript API

The component includes several JavaScript functions for interaction:

### Copy Functions
- `copyValue(value)`: Copy a value to clipboard with visual feedback
- Automatic fallback for older browsers

### Table Functions
- `sortTable(tableId, columnIndex)`: Sort table by column
- `exportTableData(tableId)`: Export table data as CSV
- `refreshTableData(tableId)`: Refresh table data

### Action Functions
- `viewRowDetails(tableId, rowIndex)`: View row details (customizable)
- `editRowData(tableId, rowIndex)`: Edit row data (customizable)

## Styling Classes

### Container Classes
- `.historical-table-container`: Main container
- `.golden-theme` / `.minimal-theme`: Theme modifiers

### Table Classes
- `.historical-table`: Base table class
- `.golden-table` / `.minimal-table`: Theme-specific table styles
- `.sortable`: Sortable column headers
- `.value-cell`: Copyable value cells
- `.change-cell`: Change indicator cells
- `.change-positive` / `.change-negative`: Color-coded changes

### State Classes
- `.empty-state`: Empty table state
- `.copied`: Copy feedback animation
- `.sorted-asc` / `.sorted-desc`: Sort direction indicators

## Responsive Behavior

### Mobile (≤ 480px)
- Stacked controls
- Reduced padding
- Smaller fonts
- Touch-optimized buttons

### Tablet (≤ 768px)
- Flexible table controls
- Optimized spacing
- Maintained functionality

### Desktop (> 768px)
- Full feature set
- Optimal spacing
- Enhanced hover effects

## Customization

### Custom CSS
Add custom styles by targeting the component classes:
```css
.historical-table-container.custom-theme {
    border: 2px solid #your-color;
}

.historical-table-container.custom-theme .table-title {
    color: #your-color;
}
```

### Custom JavaScript
Extend functionality by overriding the default functions:
```javascript
window.viewRowDetails = function(tableId, rowIndex) {
    // Your custom implementation
    openDetailModal(tableId, rowIndex);
};
```

## Browser Support

- **Modern Browsers**: Full feature support including clipboard API
- **Legacy Browsers**: Graceful fallback for copy functionality
- **Mobile Browsers**: Touch-optimized interface
- **Screen Readers**: ARIA label support

## Performance Considerations

- Efficient DOM updates
- Lazy loading for large datasets
- Optimized CSS animations
- Minimal JavaScript footprint

## Integration Examples

### With Flask/Jinja2
```python
@app.route('/market-data')
def market_data():
    data = get_market_history()
    pagination = paginate_data(data, page=request.args.get('page', 1))
    
    return render_template('market_data.html', 
                         table_data=pagination.items,
                         pagination_info=pagination)
```

### With Django
```python
def market_view(request):
    data = MarketData.objects.all()
    paginator = Paginator(data, 20)
    page = paginator.get_page(request.GET.get('page'))
    
    context = {
        'table_data': [model_to_dict(item) for item in page],
        'pagination_info': {
            'current_page': page.number,
            'total_pages': paginator.num_pages,
            # ... other pagination fields
        }
    }
    return render(request, 'template.html', context)
```

## Troubleshooting

### Common Issues

**Table not displaying data**
- Check that `table_data` is properly formatted
- Ensure `table_headers` matches data structure
- Verify template include path

**Copy function not working**
- Modern browsers require HTTPS for clipboard API
- Fallback function works in all browsers
- Check browser console for errors

**Styling issues**
- Ensure proper theme class application
- Check for CSS conflicts
- Verify responsive media queries

**Pagination not working**
- Confirm `pagination_info` object structure
- Check URL routing for pagination parameters
- Verify Flask/Django pagination setup

## Version History

- **v1.0**: Initial release with golden and minimal themes
- Features: Basic table display, sorting, export, copy functionality
- Responsive design and accessibility support

## Contributing

When modifying the component:
1. Test both themes thoroughly
2. Verify responsive behavior on all screen sizes
3. Check browser compatibility
4. Update documentation for new features
5. Maintain backward compatibility

## License

This component is part of the BFI Signals application and follows the same licensing terms.