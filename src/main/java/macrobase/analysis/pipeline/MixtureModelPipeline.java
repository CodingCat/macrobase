package macrobase.analysis.pipeline;

import macrobase.analysis.classify.BatchingPercentileClassifier;
import macrobase.analysis.classify.DumpClassifier;
import macrobase.analysis.classify.OutlierClassifier;
import macrobase.analysis.result.AnalysisResult;
import macrobase.analysis.summary.BatchSummarizer;
import macrobase.analysis.summary.Summary;
import macrobase.analysis.transform.BatchScoreFeatureTransform;
import macrobase.analysis.transform.BeforeAfterDumpingBatchScoreFeatureTransform;
import macrobase.analysis.transform.FeatureTransform;
import macrobase.analysis.transform.GridDumpingBatchScoreTransform;
import macrobase.conf.MacroBaseConf;
import macrobase.datamodel.Datum;
import macrobase.ingest.DataIngester;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.List;

public class MixtureModelPipeline extends BasePipeline {
    private static final Logger log = LoggerFactory.getLogger(MixtureModelPipeline.class);

    public Pipeline initialize(MacroBaseConf conf) throws Exception {
        super.initialize(conf);
        conf.sanityCheckBatch();
        return this;
    }

    @Override
    public AnalysisResult run() throws Exception {
        long startMs = System.currentTimeMillis();
        DataIngester ingester = conf.constructIngester();

        List<Datum> data = ingester.getStream().drain();
        long loadEndMs = System.currentTimeMillis();

        BatchScoreFeatureTransform batchTransform = new BatchScoreFeatureTransform(conf, conf.getTransformType());
        FeatureTransform gridDumpingTransform = new GridDumpingBatchScoreTransform(conf, batchTransform);
        gridDumpingTransform.initialize();
        FeatureTransform dumpingTransform = new BeforeAfterDumpingBatchScoreFeatureTransform(conf, gridDumpingTransform);
        dumpingTransform.initialize();
        dumpingTransform.consume(data);

        OutlierClassifier outlierClassifier = new BatchingPercentileClassifier(conf);
        outlierClassifier.consume(dumpingTransform.getStream().drain());

        if (conf.getBoolean(MacroBaseConf.CLASSIFIER_DUMP)) {
            String queryName = conf.getString(MacroBaseConf.QUERY_NAME);
            outlierClassifier = new DumpClassifier(conf, outlierClassifier, queryName);
        }

        BatchSummarizer summarizer = new BatchSummarizer(conf);
        summarizer.consume(outlierClassifier.getStream().drain());

        Summary result = summarizer.getStream().drain().get(0);

        final long endMs = System.currentTimeMillis();
        final long loadMs = loadEndMs - startMs;
        final long totalMs = endMs - loadEndMs;
        final long summarizeMs = result.getCreationTimeMs();
        final long executeMs = totalMs - result.getCreationTimeMs();

        log.info("took {}ms ({} tuples/sec)",
                totalMs,
                (result.getNumInliers() + result.getNumOutliers()) / (double) totalMs * 1000);

        return new AnalysisResult(result.getNumOutliers(),
                result.getNumInliers(),
                loadMs,
                executeMs,
                summarizeMs,
                result.getItemsets());
    }

}
