#include <iostream>
#include <string>
#include <random>
#include <iomanip>

// 模擬抓取與計算股票資料的結構體
struct StockData {
    std::string ticker;
    std::string name;
    double x_val;          // 法人籌碼多寡
    double y_val;          // 法人買賣超金額 (百萬)
    double x_prime;        // 良率/毛利指標 (左大右小)
    double y_prime;        // 年營收年增率 YoY (%)
    double gross_margin;   // 毛利率
    bool success;
};

// 模擬 Python 的 get_stock_data 函式
StockData getStockData(const std::string& tickerInput) {
    StockData data;
    data.ticker = tickerInput;
    
    // 簡單模擬不同代號的對應名稱與基礎數值
    if (tickerInput == "2330") {
        data.name = "台灣積體電路製造股份有限公司";
        data.gross_margin = 53.5; // 台積電高毛利
        data.x_val = 75.2;        // 法人持股高
    } else if (tickerInput == "2317") {
        data.name = "鴻海精密工業股份有限公司";
        data.gross_margin = 6.2;
        data.x_val = 45.0;
    } else {
        data.name = "範例測試股份有限公司";
        data.gross_margin = 25.0;
        data.x_val = 50.0;
    }

    // 使用隨機數模擬法人買賣超金額 (-5000 到 8000) 與營收年增率
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_real_distribution<double> dist_y(-5000.0, 8000.0);
    std::uniform_real_distribution<double> dist_rev(-10.0, 35.0);

    data.y_val = dist_y(gen);
    data.x_prime = 100.0 - data.gross_margin; // 模擬：左邊數字大代表毛利好
    data.y_prime = dist_rev(gen);
    data.success = true;

    return data;
}

int main() {
    // 設定輸出編碼支援中文（視作業系統而定）
    std::cout << "========================================\n";
    std::cout << "   🎯 C++ 智慧飆股／爛股定位篩選器診斷系統   \n";
    std::cout << "========================================\n\n";

    std::string tickerInput;
    std::cout << "請輸入台股代號 (例如: 2330, 2317): ";
    std::cin >> tickerInput;

    std::cout << "\n正在分析法人籌碼與財報數據...\n\n";

    StockData data = getStockData(tickerInput);

    if (!data.success) {
        std::cout << "❌ 無法取得資料，請檢查代號是否正確。\n";
    } else {
        std::cout << "✅ 成功載入：" << data.name << " (" << tickerInput << ")\n";
        std::cout << "----------------------------------------\n";
        
        // 顯示詳細數據卡片
        std::cout << std::fixed << std::setprecision(2);
        std::cout << "📊 【詳細數據診斷報告】\n";
        std::cout << "• 法人籌碼 X 軸分數      : " << data.x_val << "\n";
        std::cout << "• 良率指標 x' 軸 (左大右小): " << data.x_prime << "\n";
        std::cout << "• 年營收年增率 y' 軸     : " << data.y_prime << "%\n";
        std::cout << "• 法人近期買賣超金額     : " << data.y_val << " 百萬\n";
        std::cout << "----------------------------------------\n";

        // 系統診斷解讀（對應 Python 的 if-else 邏輯）
        std::cout << "💡 【系統診斷解讀】\n";
        if (data.x_val > 50.0 && data.y_val > 0.0) {
            std::cout << "🎯 【潛力飆股區（第一象限）】\n";
            std::cout << "   -> 法人籌碼集中且持續買超！且其良率與年營收正向發展，屬於強勢優質標的。\n";
        } else if (data.x_val < 50.0 && data.y_val < 0.0) {
            std::cout << "⚠️ 【弱勢爛股區（第三象限）】\n";
            std::cout << "   -> 法人籌碼稀疏且持續賣超，基本面與籌碼面雙重弱勢，需嚴加防範。\n";
        } else {
            std::cout << "⚖️ 【震盪整理區】\n";
            std::cout << "   -> 多空交雜或法人籌碼尚未凝聚，建議搭配技術面多加觀察。\n";
        }
    }

    std::cout << "========================================\n";
    return 0;
}
