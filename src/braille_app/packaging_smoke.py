"""Opt-in packaged-app test using the normal GUI worker and result rendering."""
import argparse,json,sys
from pathlib import Path
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QLabel

def run(app,window,arguments):
    parser=argparse.ArgumentParser()
    parser.add_argument('--packaging-smoke',action='store_true')
    parser.add_argument('--master',required=True)
    parser.add_argument('--braille',required=True)
    parser.add_argument('--result',required=True)
    args=parser.parse_args(arguments)
    dest=Path(args.result);dest.parent.mkdir(parents=True,exist_ok=True)
    state={'done':False}
    def finish(error=None):
        if state['done']:return
        state['done']=True
        r=window.current_result
        report={'executable':sys.executable,'frozen':bool(getattr(sys,'frozen',False)),
                'error':error,'statistics':r.statistics if r else None,
                'title':window.res_title.text(),'error_summary':window.error_summary.text(),
                'visible_labels':[x.text() for x in window.findChildren(QLabel) if x.isVisible()],
                'annotated_pdf':window.annotated_pdf_path,'report':window.report_path,
                'diagnostic_report':window.diagnostic_report_path,
                'annotation_error':window.thread.annotation_error if window.thread else None,
                'open_annotated_enabled':window.open_annotated_btn.isEnabled(),
                'issue_group_count':window.issue_tree.topLevelItemCount(),
                'issue_count':sum(window.issue_tree.topLevelItem(i).childCount() for i in range(window.issue_tree.topLevelItemCount()))}
        window.grab().save(str(dest.with_suffix('.png')))
        if report['issue_count']:
            first=window.issue_tree.topLevelItem(0).child(0)
            window.issue_tree.setCurrentItem(first)
            report['selected_issue_details']=window.detail_text.toPlainText()
            window.grab().save(str(dest.with_name(dest.stem+'_details.png')))
        dest.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
        if window.thread:window.thread.wait(10000)
        app.exit(1 if error or report['annotation_error'] else 0)
    def start():
        window.english_path=args.master;window.braille_path=args.braille
        window.on_error=lambda message:finish(message)
        window.grab().save(str(dest.with_name(dest.stem+'_upload.png')))
        window.run_btn.click()
        window.thread.finished.connect(lambda _result:QTimer.singleShot(150,finish))
    QTimer.singleShot(0,start)
    QTimer.singleShot(120000,lambda:finish('Packaging smoke timed out'))
    return app.exec()
