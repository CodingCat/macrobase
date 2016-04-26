package macrobase.analysis.classify;

import macrobase.analysis.result.OutlierClassificationResult;
import macrobase.conf.MacroBaseConf;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.BufferedWriter;
import java.io.FileWriter;
import java.io.IOException;
import java.io.PrintWriter;

/**
 * Transparently dumps classifier output by wrapping another classifier and copying its
 * results to a file.
 */
public class DumpClassifier implements OutlierClassifier {
    private static final Logger log = LoggerFactory.getLogger(DumpClassifier.class);
    protected OutlierClassifier input = null;
    protected MacroBaseConf conf;
    private PrintWriter out;
    private int count;

    private String filepath;

    public DumpClassifier(MacroBaseConf conf, OutlierClassifier input) throws IOException {
        this(conf, input, "default");
    }

    public DumpClassifier(MacroBaseConf conf, OutlierClassifier input, String name) throws IOException {
        this.conf = conf;
        this.input = input;
        filepath = String.format("test_out/dump_classifier_%s.txt", name);
        out = new PrintWriter(new BufferedWriter(new FileWriter(filepath)));
    }

    public String getFilePath(){
        return filepath;
    }

    public boolean hasNext() {
        boolean hasNext = input.hasNext();
        if (!hasNext) {
            out.close();
        }
        return hasNext;
    }

    public OutlierClassificationResult next() {
        OutlierClassificationResult res = input.next();
        int flag = 0;
        if (res.isOutlier()) {
            flag = 1;
        }
        out.format("%d,%d\n", count, flag);

        count++;
        return res;
    }
}