# Endianness Detection in ARS Socket Reader

## The Problem

In the original implementations, endianness was handled in one of these ways:

1. **Hardcoded assumption**: `is_big_endian: bool = False` (always little-endian)
2. **Manual configuration**: User had to specify endianness manually
3. **No detection**: Could lead to incorrect data interpretation

## The Solution: Automatic Endianness Detection

The new `ars_socket_reader_endianness.py` implements **automatic endianness detection** using multiple detection methods:

### Detection Methods

#### 1. **Range-Based Detection**
```python
def _detect_by_range(self, samples: List[bytes]) -> Dict:
    """Detect endianness by analyzing value ranges"""
    
    # Parse samples as both little-endian and big-endian
    le_value = struct.unpack('<d', sample)[0]  # Little endian
    be_value = struct.unpack('>d', sample)[0]  # Big endian
    
    # Check for reasonable angular rate ranges (±1000 rad/s)
    le_reasonable = all(abs(v) < 1000 for v in little_endian_values)
    be_reasonable = all(abs(v) < 1000 for v in big_endian_values)
    
    # Check for NaN/infinity
    le_valid = all(v == v and abs(v) != float('inf') for v in little_endian_values)
    be_valid = all(v == v and abs(v) != float('inf') for v in big_endian_values)
```

**How it works**: Rate sensor data should be in reasonable ranges. If one endianness produces values like 1e300 or NaN, it's likely wrong.

#### 2. **Pattern-Based Detection**
```python
def _detect_by_pattern(self, samples: List[bytes]) -> Dict:
    """Detect endianness by analyzing byte patterns"""
    
    # Check for patterns that suggest valid IEEE 754 doubles
    le_pattern_score = self._analyze_byte_pattern(le_bytes)
    be_pattern_score = self._analyze_byte_pattern(be_bytes)
```

**How it works**: Analyzes byte patterns to detect valid IEEE 754 double-precision floating-point format.

#### 3. **Consistency-Based Detection**
```python
def _detect_by_consistency(self, samples: List[bytes]) -> Dict:
    """Detect endianness by checking consistency over time"""
    
    # Check for reasonable variation (rate sensor data should vary smoothly)
    le_variation = self._calculate_variation(little_endian_values)
    be_variation = self._calculate_variation(big_endian_values)
    
    # Lower variation suggests more consistent (and likely correct) data
    if le_variation < be_variation:
        return {'is_big_endian': False, 'confidence': 1.0 - le_variation}
```

**How it works**: Rate sensor data should vary smoothly over time. Erratic values suggest wrong endianness.

### Detection Process

1. **Sample Collection**: Collects configurable number of samples (default: 50)
2. **Multi-Method Analysis**: Runs all three detection methods
3. **Voting System**: Combines results from all methods
4. **Confidence Scoring**: Provides confidence level (0.0 to 1.0)
5. **Fallback Handling**: Uses fallback logic if detection confidence is low

### Usage Example

```bash
python ars_socket_reader_endianness.py --ip 192.168.1.100 --start-port 5000 --detection-samples 50
```

### Output Example

```
=== Endianness Detection ===
Detected ports: 12/12
Port 0: Little Endian (confidence: 0.95, method: range_analysis)
Port 1: Little Endian (confidence: 0.92, method: consistency_analysis)
Port 2: Little Endian (confidence: 0.88, method: pattern_analysis)
Port 3: Little Endian (confidence: 0.94, method: range_analysis)
...
```

## Detection Confidence Levels

| Confidence | Interpretation | Action |
|------------|----------------|---------|
| 0.9 - 1.0 | Very High | Use detected endianness |
| 0.7 - 0.9 | High | Use detected endianness |
| 0.5 - 0.7 | Medium | Use detected endianness with warning |
| 0.3 - 0.5 | Low | Use fallback logic |
| 0.0 - 0.3 | Very Low | Use fallback logic |

## Fallback Logic

When detection confidence is low, the system uses fallback logic:

```python
# Fallback: try both and pick the more reasonable one
le_value = struct.unpack('<d', data)[0]
be_value = struct.unpack('>d', data)[0]

# Choose the more reasonable value
le_reasonable = abs(le_value) < 1000 and le_value == le_value and abs(le_value) != float('inf')
be_reasonable = abs(be_value) < 1000 and be_value == be_value and abs(be_value) != float('inf')

if le_reasonable and not be_reasonable:
    is_big_endian = False
elif be_reasonable and not le_reasonable:
    is_big_endian = True
else:
    # Default to little endian if both are reasonable
    is_big_endian = False
```

## Configuration Options

### Command Line Arguments

- `--detection-samples`: Number of samples to collect for detection (default: 50)
- `--debug`: Enable debug logging to see detection process

### Detection Parameters

- **Sample Size**: More samples = higher confidence (but slower detection)
- **Range Threshold**: Maximum reasonable value for rate sensor data
- **Confidence Threshold**: Minimum confidence to use detected endianness

## Comparison with Previous Versions

| Version | Endianness Handling | Detection Method | Confidence |
|---------|-------------------|------------------|------------|
| Original | Hardcoded (little-endian) | None | N/A |
| Enhanced | Manual configuration | None | N/A |
| Endianness | Automatic detection | Multi-method | 0.0-1.0 |

## Benefits

1. **Automatic**: No manual configuration required
2. **Robust**: Multiple detection methods with voting
3. **Confident**: Provides confidence scores
4. **Fallback**: Handles edge cases gracefully
5. **Per-Port**: Each port can have different endianness
6. **Real-time**: Continuous monitoring and adjustment

## Limitations

1. **Sample Requirements**: Needs sufficient samples for reliable detection
2. **Data Quality**: Requires reasonable data ranges for detection
3. **Performance**: Slight overhead for detection calculations
4. **Edge Cases**: May struggle with very noisy or corrupted data

## Best Practices

1. **Start with Default**: Use default detection samples (50) initially
2. **Monitor Confidence**: Watch confidence levels in output
3. **Adjust Samples**: Increase samples if confidence is low
4. **Verify Results**: Cross-check detected endianness with known data
5. **Handle Edge Cases**: Be prepared for fallback scenarios

## Integration

The endianness detection can be integrated with the existing rate sensor simulator:

```python
# Get endianness detection results
endianness_report = reader.get_endianness_report()

# Use detected endianness for data conversion
for port_idx, detection in endianness_report['detections'].items():
    if detection['confidence'] > 0.7:
        is_big_endian = detection['is_big_endian']
        # Use detected endianness for this port
```

This provides a robust, automatic solution for handling endianness in ARS sensor data without requiring manual configuration or assumptions.


