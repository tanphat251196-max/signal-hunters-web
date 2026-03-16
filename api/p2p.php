<?php
/**
 * USDT/VND P2P Proxy — daututhongminh24h.com
 * Fetch giá P2P Binance server-side (bypass CORS)
 * Cache 10 phút trong file
 */

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Cache-Control: public, max-age=600');

$cache_file = sys_get_temp_dir() . '/p2p_cache.json';
$cache_ttl  = 600; // 10 phút

// Trả cache nếu còn mới
if (file_exists($cache_file) && (time() - filemtime($cache_file)) < $cache_ttl) {
    echo file_get_contents($cache_file);
    exit;
}

// Fetch Binance P2P
$url  = 'https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search';
$body = json_encode([
    'asset'         => 'USDT',
    'fiat'          => 'VND',
    'tradeType'     => 'BUY',
    'page'          => 1,
    'rows'          => 5,
    'payTypes'      => [],
    'countries'     => [],
    'publisherType' => null,
]);

$opts = [
    'http' => [
        'method'  => 'POST',
        'header'  => implode("\r\n", [
            'Content-Type: application/json',
            'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
        ]),
        'content' => $body,
        'timeout' => 10,
    ],
];

$response = @file_get_contents($url, false, stream_context_create($opts));

if (!$response) {
    // Fallback: trả cache cũ nếu có
    if (file_exists($cache_file)) {
        echo file_get_contents($cache_file);
    } else {
        echo json_encode(['price' => 0, 'change' => 0, 'updated' => date('H:i'), 'source' => 'error']);
    }
    exit;
}

$data = json_decode($response, true);
$ads  = $data['data'] ?? [];

if (empty($ads)) {
    echo json_encode(['price' => 0, 'change' => 0, 'updated' => date('H:i'), 'source' => 'empty']);
    exit;
}

$prices = array_map(fn($a) => (float)($a['adv']['price'] ?? 0), $ads);
$prices = array_filter($prices);
$avg    = count($prices) ? array_sum($prices) / count($prices) : 0;

$result = json_encode([
    'price'   => round($avg),
    'change'  => 0,
    'updated' => date('H:i'),
    'source'  => 'binance_p2p',
]);

// Lưu cache
file_put_contents($cache_file, $result);
echo $result;
