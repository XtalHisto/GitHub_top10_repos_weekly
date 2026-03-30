import smtplib
from omegaconf import OmegaConf
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.header import Header
from email.utils import formataddr


class Emailer:
    def __init__(self, cfg):
        self.cfg = cfg
        self.smtp = {
            'host': self.cfg.email.smtp_host,
            'port': self.cfg.email.smtp_port,
            'user': self.cfg.email.smtp_user,
            'pswd': self.cfg.email.smtp_pswd,
            'nickname':self.cfg.email.smtp_nickname,
        }
        # 初始化所有收件人
        self.reciever = [
            {"name": person.name, "adrs": person.email_address}
            for person in self.cfg.recipient
        ]

   
    def img_attacher(self,  html_file):
        msg = MIMEMultipart("related")
        msg.attach(MIMEText(html_file, 'html', "utf-8"))
        with open(self.cfg.img.path, 'rb') as f:
            img = MIMEImage(f.read())
            img.add_header("Content-ID", f"<{self.cfg.img.cid}>")
            img.add_header('Content-Disposition', 'inline')
            msg.attach(img)
        return msg


    def email_send(self, html):
        # 创建邮件对象
        self.msg = self.img_attacher(html)

        # 发件人显示名
        self.msg["From"] = formataddr((str(Header(self.smtp['nickname'], "utf-8")), self.smtp['user']))

        # 收件人列表
        to_list = [r["adrs"] for r in self.reciever]

        # 收件人显示
        to_header = ",".join([
            formataddr((str(Header(r["name"], "utf-8")), r["adrs"]))
            for r in self.reciever
        ])
        self.msg["To"] = to_header

        # 主题
        self.msg["Subject"] = Header("GitHub star数增长情况周报", "utf-8")

        try:
            # 连接邮件服务器并登录
            smtp_connection = smtplib.SMTP(self.smtp['host'], self.smtp['port'])
            smtp_connection.login(self.smtp['user'], self.smtp['pswd'])

            # 发送邮件
            smtp_connection.sendmail(
                self.smtp['user'],
                to_list,
                self.msg.as_string()
            )

            # 关闭连接
            smtp_connection.quit()

            print("邮件发送成功！")

        except Exception as e:
            print("邮件发送失败：", e)
    

    def email_send_file(self, html_file):
        # 创建邮件对象
        with open(html_file, "r", encoding="utf-8") as f:
            html = f.read()

        self.msg = self.img_attacher(html)

        # 发件人显示名
        self.msg["From"] = formataddr((str(Header(self.smtp['nickname'], "utf-8")), self.smtp['user']))

        # 收件人列表
        to_list = [r["adrs"] for r in self.reciever]

        # 收件人显示
        to_header = ",".join([
            formataddr((str(Header(r["name"], "utf-8")), r["adrs"]))
            for r in self.reciever
        ])
        self.msg["To"] = to_header

        # 主题
        self.msg["Subject"] = Header("GitHub star数增长情况周报", "utf-8")

        try:
            # 连接邮件服务器并登录
            smtp_connection = smtplib.SMTP(self.smtp['host'], self.smtp['port'])
            smtp_connection.login(self.smtp['user'], self.smtp['pswd'])

            # 发送邮件
            smtp_connection.sendmail(
                self.smtp['user'],
                to_list,
                self.msg.as_string()
            )

            # 关闭连接
            smtp_connection.quit()

            print("邮件发送成功！")

        except Exception as e:
            print("邮件发送失败：", e)


if __name__ == "__main__":
    cfg = OmegaConf.load("config.yaml")
    sender = Emailer(cfg)
    sender.email_send_file('test.html')