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

// Fetch OKX P2P (Binance block server-side request, OKX không)
$url  = 'https://www.okx.com/v3/c2c/tradingOrders/books?quoteCurrency=VND&baseCurrency=USDT&side=buy&paymentMethod=all&userType=all&showTrade=false&showFollow=false&showAlreadyTraded=false&isAbleFilter=false';
$body = null;

$opts = [
    'http' => [
        'method'  => 'GET',
        'header'  => implode("\r\n", [
            'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36',
            'Accept: application/json',
        ]),
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
$ads  = $data['data']['buy'] ?? [];

if (empty($ads)) {
    echo json_encode(['price' => 0, 'change' => 0, 'updated' => date('H:i'), 'source' => 'empty']);
    exit;
}

$prices = array_map(fn($a) => (float)($a['price'] ?? 0), $ads);
$prices = array_filter($prices);
$avg    = count($prices) ? array_sum($prices) / count($prices) : 0;

$result = json_encode([
    'price'   => round($avg),
    'change'  => 0,
    'updated' => date('H:i'),
    'source'  => 'okx_p2p',
]);

// Lưu cache
file_put_contents($cache_file, $result);
echo $result;
