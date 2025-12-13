# 文件名: login_script.py
# 作用: 使用 Playwright 模拟浏览器，完成 ClawCloud 的 GitHub 授权登录

import os
import time
from playwright.sync_api import sync_playwright

def run_login():
    # 从环境变量中获取 GitHub 账号和密码
    # 这些环境变量会在 GitHub Actions 工作流中注入
    username = os.environ.get("GH_USERNAME")
    password = os.environ.get("GH_PASSWORD")

    if not username or not password:
        print("错误: 未找到 GH_USERNAME 或 GH_PASSWORD 环境变量。")
        return

    print("启动浏览器...")
    # 使用 sync_playwright 上下文管理器启动 Playwright
    with sync_playwright() as p:
        # 启动 Chromium 浏览器 (headless=True 表示无头模式，不在界面显示，适合服务器运行)
        browser = p.chromium.launch(headless=True)
        # 创建一个新的浏览器上下文（相当于一个新的浏览器窗口，没有任何缓存）
        context = browser.new_context()
        page = context.new_page()

        # 1. 访问 ClawCloud 目标网址
        target_url = "https://ap-northeast-1.run.claw.cloud/"
        print(f"正在访问: {target_url}")
        page.goto(target_url)
        
        # 等待页面加载，防止网络延迟
        page.wait_for_load_state("networkidle")

        # 2. 检测是否需要登录
        # 逻辑: 如果网址被重定向到了 console 或者 login 页面，或者页面上有“GitHub”字样
        # 注意: 这里的判断逻辑是根据常见 OAuth 流程编写的
        
        # 尝试寻找页面上包含 "GitHub" 文本的登录按钮并点击
        # 如果已经登录，这步可能会超时，所以我们用 try-except 包裹
        try:
            # 这里的选择器意思是：查找页面上包含 "GitHub" 字样的按钮或链接
            # ClawCloud 的登录页通常会有一个 "Sign in with GitHub" 按钮
            login_button = page.get_by_text("GitHub", exact=False)
            
            if login_button.count() > 0:
                print("检测到 GitHub 登录按钮，准备点击...")
                login_button.first.click()
            else:
                print("未在首页直接检测到明确的 GitHub 按钮，检查是否已重定向到 GitHub...")
        except Exception as e:
            print(f"寻找登录按钮时发生轻微错误 (可能是已经跳转): {e}")

        # 3. 处理 GitHub 登录页面
        # 给一点时间让页面跳转到 GitHub
        page.wait_for_timeout(3000) 

        if "github.com/login" in page.url or "github.com/session" in page.url:
            print("已到达 GitHub 登录页面。")
            
            # 填写 GitHub 用户名
            # selector '#login_field' 是 GitHub 登录框的固定 ID
            page.fill("#login_field", username)
            
            # 填写 GitHub 密码
            # selector '#password' 是 GitHub 密码框的固定 ID
            page.fill("#password", password)
            
            print("正在提交登录表单...")
            # 点击登录按钮 'input[name="commit"]' 是 GitHub 登录按钮的选择器
            page.click("input[name='commit']")
            
            # 等待登录后的跳转
            page.wait_for_load_state("networkidle")
        else:
            print(f"当前页面 URL: {page.url}，似乎没有跳转到 GitHub 登录页，可能已经登录或页面结构不同。")

        # 4. 处理 "Authorize App" (应用授权) 页面
        # 如果是第一次登录，GitHub 会询问 "是否授权 ClawCloud 访问您的账号？"
        if "github.com" in page.url and "authorize" in page.url:
            print("检测到应用授权请求，尝试点击授权按钮...")
            # 尝试点击绿色的授权按钮 (通常包含 "Authorize" 文本)
            try:
                page.click("button:has-text('Authorize')", timeout=5000)
            except:
                print("未找到授权按钮，或者已自动跳过。")

        # 5. 验证结果
        # 等待最终跳转回 ClawCloud
        print("等待最终跳转...")
        time.sleep(5) # 强制等待几秒
        
        final_url = page.url
        print(f"最终页面 URL: {final_url}")

        # 截图保存，方便在 GitHub Actions 的 Artifacts 中查看结果（用于调试）
        page.screenshot(path="login_result.png")
        print("已保存截图 login_result.png")

        if "claw.cloud" in final_url and "login" not in final_url:
            print("✅ 登录成功！已返回 ClawCloud 页面。")
        else:
            print("⚠️ 登录可能未完成，请检查截图。")

        # 关闭浏览器
        browser.close()

if __name__ == "__main__":
    run_login()
