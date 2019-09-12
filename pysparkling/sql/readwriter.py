import sys
from pysparkling import RDD
from pysparkling.sql.internal_utils.readers import CSVReader, JSONReader, InternalReader
from pysparkling.sql.internal_utils.readwrite import OptionUtils, to_option_stored_value
from pysparkling.sql.internal_utils.writers import CSVWriter
from pysparkling.sql.utils import IllegalArgumentException

WRITE_MODES = ("overwrite", "append", "ignore", "error", "errorifexists")
DATA_WRITERS = dict(
    csv=CSVWriter,
)
if sys.version >= '3':
    basestring = unicode = str


class DataFrameReader(OptionUtils):
    def option(self, k, v):
        self._jreader.option(k, v)
        return self

    def schema(self, schema):
        self._jreader.schema(schema)
        return self

    def __init__(self, spark):
        """

        :type spark: pysparkling.sql.session.SparkSession
        """
        self._jreader = InternalReader(spark)
        self._spark = spark

    def _df(self, jdf):
        from pysparkling.sql.dataframe import DataFrame
        return DataFrame(jdf, self._spark)

    def csv(self, path, schema=None, sep=None, encoding=None, quote=None, escape=None,
            comment=None, header=None, inferSchema=None, ignoreLeadingWhiteSpace=None,
            ignoreTrailingWhiteSpace=None, nullValue=None, nanValue=None, positiveInf=None,
            negativeInf=None, dateFormat=None, timestampFormat=None, maxColumns=None,
            maxCharsPerColumn=None, maxMalformedLogPerPartition=None, mode=None,
            columnNameOfCorruptRecord=None, multiLine=None, charToEscapeQuoteEscaping=None,
            samplingRatio=None, enforceSchema=None, emptyValue=None, locale=None, lineSep=None):
        self._set_opts(
            schema=schema, sep=sep, encoding=encoding, quote=quote, escape=escape, comment=comment,
            header=header, inferSchema=inferSchema, ignoreLeadingWhiteSpace=ignoreLeadingWhiteSpace,
            ignoreTrailingWhiteSpace=ignoreTrailingWhiteSpace, nullValue=nullValue,
            nanValue=nanValue, positiveInf=positiveInf, negativeInf=negativeInf,
            dateFormat=dateFormat, timestampFormat=timestampFormat, maxColumns=maxColumns,
            maxCharsPerColumn=maxCharsPerColumn,
            maxMalformedLogPerPartition=maxMalformedLogPerPartition, mode=mode,
            columnNameOfCorruptRecord=columnNameOfCorruptRecord, multiLine=multiLine,
            charToEscapeQuoteEscaping=charToEscapeQuoteEscaping, samplingRatio=samplingRatio,
            enforceSchema=enforceSchema, emptyValue=emptyValue, locale=locale, lineSep=lineSep
        )
        if isinstance(path, basestring):
            path = [path]
        if type(path) == list:
            return self._df(self._jreader.csv(path))
        elif isinstance(path, RDD):
            return self._df(self._jreader.csv(path.collect()))
        else:
            raise TypeError("path can be only string, list or RDD")

    def json(self, path, schema=None, primitivesAsString=None, prefersDecimal=None,
             allowComments=None, allowUnquotedFieldNames=None, allowSingleQuotes=None,
             allowNumericLeadingZero=None, allowBackslashEscapingAnyCharacter=None,
             mode=None, columnNameOfCorruptRecord=None, dateFormat=None, timestampFormat=None,
             multiLine=None, allowUnquotedControlChars=None, lineSep=None, samplingRatio=None,
             dropFieldIfAllNull=None, encoding=None, locale=None):
        self._set_opts(
            schema=schema, primitivesAsString=primitivesAsString, prefersDecimal=prefersDecimal,
            allowComments=allowComments, allowUnquotedFieldNames=allowUnquotedFieldNames,
            allowSingleQuotes=allowSingleQuotes, allowNumericLeadingZero=allowNumericLeadingZero,
            allowBackslashEscapingAnyCharacter=allowBackslashEscapingAnyCharacter,
            mode=mode, columnNameOfCorruptRecord=columnNameOfCorruptRecord, dateFormat=dateFormat,
            timestampFormat=timestampFormat, multiLine=multiLine,
            allowUnquotedControlChars=allowUnquotedControlChars, lineSep=lineSep,
            samplingRatio=samplingRatio, dropFieldIfAllNull=dropFieldIfAllNull, encoding=encoding,
            locale=locale)
        if isinstance(path, basestring):
            path = [path]
        if type(path) == list:
            return self._df(self._jreader.json(path))
        elif isinstance(path, RDD):
            return self._df(self._jreader.json(path.collect()))
        else:
            raise TypeError("path can be only string, list or RDD")


class InternalWriter(object):
    def __init__(self, df):
        self._df = df
        self._source = "parquet"
        self._mode = "errorifexists"
        self._options = {}
        self._partitioning_col_names = None
        self._num_buckets = None
        self._bucket_col_names = None
        self._sort_col_names = None

    def option(self, k, v):
        self._options[k.lower()] = to_option_stored_value(v)

    def mode(self, mode):
        if mode not in WRITE_MODES:
            raise IllegalArgumentException(
                "Unknown save mode: . Accepted save modes are {0}.".format(
                    "', '".join(WRITE_MODES)
                )
            )
        self._mode = mode

    def format(self, source):
        self._source = source
        return self

    def partitionBy(self, partitioning_col_names):
        self._partitioning_col_names = partitioning_col_names

    def bucketBy(self, num_buckets, *bucket_cols):
        self._num_buckets = num_buckets
        self._bucket_col_names = bucket_cols

    def sortBy(self, sort_cols):
        self._sort_col_names = sort_cols

    def save(self, path=None):
        Writer = DATA_WRITERS[self._source]
        self.option("path", path)
        Writer(
            self._df,
            self._mode,
            self._options,
            self._partitioning_col_names,
            self._num_buckets,
            self._bucket_col_names,
            self._sort_col_names
        ).save()

    def insertInto(self, tableName=None):
        raise NotImplementedError("Pysparkling does not implement write to table yet")

    def saveAsTable(self, name):
        raise NotImplementedError("Pysparkling does not implement write to table yet")

    def json(self, path):
        return self.format("json").save(path)

    def parquet(self, path):
        raise NotImplementedError("Pysparkling does not implement write to parquet yet")

    def text(self, path):
        raise NotImplementedError("Pysparkling does not implement write to text yet")

    def csv(self, path):
        return self.format("csv").save(path)

    def orc(self, path):
        raise NotImplementedError("Pysparkling does not implement write to ORC")

    def jdbc(self, path):
        raise NotImplementedError("Pysparkling does not implement write to JDBC")


class DataFrameWriter(OptionUtils):
    def __init__(self, df):
        self._df = df
        self._spark = df.sql_ctx
        self._jwrite = InternalWriter(self._df)

    def mode(self, saveMode):
        # At the JVM side, the default value of mode is already set to "error".
        # So, if the given saveMode is None, we will not call JVM-side's mode method.
        if saveMode is not None:
            self._jwrite = self._jwrite.mode(saveMode)
        return self

    def format(self, source):
        self._jwrite = self._jwrite.format(source)
        return self

    def option(self, key, value):
        self._jwrite.option(key, value)
        return self

    def options(self, **options):
        for k in options:
            self._jwrite.option(k, options[k])
        return self

    def partitionBy(self, *cols):
        if len(cols) == 1 and isinstance(cols[0], (list, tuple)):
            cols = cols[0]
        self._jwrite = self._jwrite.partitionBy(cols)
        return self

    def bucketBy(self, numBuckets, col, *cols):
        if not isinstance(numBuckets, int):
            raise TypeError("numBuckets should be an int, got {0}.".format(type(numBuckets)))

        if isinstance(col, (list, tuple)):
            if cols:
                raise ValueError("col is a {0} but cols are not empty".format(type(col)))

            cols = col
        else:
            cols = [col] + list(cols)

        if not all(isinstance(c, basestring) for c in cols):
            raise TypeError("all names should be `str`")

        self._jwrite = self._jwrite.bucketBy(numBuckets, *cols)
        return self

    def sortBy(self, col, *cols):
        if isinstance(col, (list, tuple)):
            if cols:
                raise ValueError("col is a {0} but cols are not empty".format(type(col)))

            col, cols = col[0], col[1:]

        if not all(isinstance(c, basestring) for c in cols) or not (isinstance(col, basestring)):
            raise TypeError("all names should be `str`")

        self._jwrite = self._jwrite.sortBy(col, *cols)
        return self

    def save(self, path=None, format=None, mode=None, partitionBy=None, **options):
        self.mode(mode).options(**options)
        if partitionBy is not None:
            self.partitionBy(partitionBy)
        if format is not None:
            self.format(format)
        if path is None:
            self._jwrite.save()
        else:
            self._jwrite.save(path)

    def json(self, path, mode=None, compression=None, dateFormat=None, timestampFormat=None,
             lineSep=None, encoding=None):
        self.mode(mode)
        self._set_opts(
            compression=compression, dateFormat=dateFormat, timestampFormat=timestampFormat,
            lineSep=lineSep, encoding=encoding)
        self._jwrite.json(path)

    def csv(self, path, mode=None, compression=None, sep=None, quote=None, escape=None,
            header=None, nullValue=None, escapeQuotes=None, quoteAll=None, dateFormat=None,
            timestampFormat=None, ignoreLeadingWhiteSpace=None, ignoreTrailingWhiteSpace=None,
            charToEscapeQuoteEscaping=None, encoding=None, emptyValue=None, lineSep=None):
        self.mode(mode)
        self._set_opts(compression=compression, sep=sep, quote=quote, escape=escape, header=header,
                       nullValue=nullValue, escapeQuotes=escapeQuotes, quoteAll=quoteAll,
                       dateFormat=dateFormat, timestampFormat=timestampFormat,
                       ignoreLeadingWhiteSpace=ignoreLeadingWhiteSpace,
                       ignoreTrailingWhiteSpace=ignoreTrailingWhiteSpace,
                       charToEscapeQuoteEscaping=charToEscapeQuoteEscaping,
                       encoding=encoding, emptyValue=emptyValue, lineSep=lineSep)
        self._jwrite.csv(path)

    def insertInto(self, tableName=None):
        raise NotImplementedError("Pysparkling does not implement write to table yet")

    def saveAsTable(self, name):
        raise NotImplementedError("Pysparkling does not implement write to table yet")

    def parquet(self, path):
        raise NotImplementedError("Pysparkling does not implement write to parquet yet")

    def text(self, path):
        raise NotImplementedError("Pysparkling does not implement write to text yet")

    def orc(self, path):
        raise NotImplementedError("Pysparkling does not implement write to ORC")

    def jdbc(self, path):
        raise NotImplementedError("Pysparkling does not implement write to JDBC")
