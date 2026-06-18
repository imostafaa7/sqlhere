طريقة التثبيت على Kali:

cat > ~/Tools/sqlhere << 'EOF'
# الصق الكود كاملاً من فوق
EOF
chmod +x ~/Tools/sqlhere
sudo ln -sf ~/Tools/sqlhere /usr/local/bin/sqlhere

تنفيذ متوازي: katana + hakrawler + waymore يشتغلون سوية (ThreadPoolExecutor)
توقيت لكل أمر: [12:34:56] قبل كل رسالة
built-in dedup: إذا uro مش موجود، يستخدم dedup مدمج
timeout قابل للتعديل: --timeout 300
إصلاح katana: أزلت -kf نهائياً
إصلاح waymore: 3 مسارات بديلة لملف المخرجات
أنظف وأسرع: 451 سطر بدلاً من 520
أمثلة:

sqlhere -d target.com                          # فحص كامل
sqlhere -d target.com --gf xss                  # بحث عن XSS بدل SQLi
sqlhere -l targets.txt --threads 50 --depth 5   # أهداف متعددة
sqlhere -d target.com --resume                  # استئناف الفحص
sqlhere --sqlmap-only urls.txt                  # sqlmap مباشر
sqlhere -d target.com -q                        # وضع هادئ
