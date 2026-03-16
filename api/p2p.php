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

// Fetch Binance P2P trực tiếp (skip ad đầu tiên)
$url  = 'https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search';
$body = json_encode([
    'page'          => 1,
    'rows'          => 10,
    'payTypes'      => [],
    'asset'         => 'USDT',
    'fiat'          => 'VND',
    'tradeType'     => 'BUY',
    'publisherType' => null,
]);

$opts = [
    'http' => [
        'method'  => 'POST',
        'header'  => implode("\r\n", [
            'Content-Type: application/json',
            'Accept-Encoding: identity',
            'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36',
            'Origin: https://p2p.binance.com',
            'Referer: https://p2p.binance.com/trade/all-payments/USDT?fiat=VND',
            'clienttype: web',
        ]),
        'content' => $body,
        'timeout' => 10,
    ],
];

$response = @file_get_contents($url, false, stream_context_create($opts));

if (!$response) {
    if (file_exists($cache_file)) {
        echo file_get_contents($cache_file);
    } else {
        echo json_encode(['price' => 0, 'change' => 0, 'updated' => date('H:i'), 'source' => 'error']);
    }
    exit;
}

$data = json_decode($response, true);
$ads  = $data['data'] ?? [];

// Bỏ qua ad đầu tiên (quảng cáo), lấy từ index 1
if (count($ads) > 1) {
    $ads = array_slice($ads, 1);
}

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
