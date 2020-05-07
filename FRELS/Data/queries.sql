select t.range as range, count(*) as nbOcc
from (
  select case  
    when distance between 0 and 99 then ' 0- 99'
    when distance between 100 and 199 then '100-199'
    when distance between 200 and 299 then '200-299'
    else '>=300' end as range
  from flights_150k where distance between 0 and 1000) t
group by t.range;



select t.range as range, count(*) as nbOcc from (
    select case  
        when SecurityDelay > 6.000000 and SecurityDelay <= 6.200000 then 'ls0'
        when SecurityDelay >= 12.000000 and SecurityDelay < 12.400000 then 'rs0' 
        when SecurityDelay > 6.200000 and SecurityDelay <= 6.400000 then 'ls1' 
        when SecurityDelay >= 12.400000 and SecurityDelay < 12.800000 then 'rs1' 
        when SecurityDelay > 6.400000 and SecurityDelay <= 6.600000 then 'ls2' 
        when SecurityDelay >= 12.800000 and SecurityDelay < 13.200000 then 'rs2' 
        when SecurityDelay > 6.600000 and SecurityDelay <= 6.800000 then 'ls3' 
        when SecurityDelay >= 13.200000 and SecurityDelay < 13.600000 then 'rs3' 
        when SecurityDelay > 6.800000 and SecurityDelay <= 7.000000 then 'ls4' 
        when SecurityDelay >= 13.600000 and SecurityDelay < 14.000000 then 'rs4' 
        when SecurityDelay > 7.000000 and SecurityDelay <= 7.200000 then 'ls5' 
        when SecurityDelay >= 14.000000 and SecurityDelay < 14.400000 then 'rs5' 
        when SecurityDelay > 7.200000 and SecurityDelay <= 7.400000 then 'ls6' 
        when SecurityDelay >= 14.400000 and SecurityDelay < 14.800000 then 'rs6' 
        when SecurityDelay > 7.400000 and SecurityDelay <= 7.600000 then 'ls7' 
        when SecurityDelay >= 14.800000 and SecurityDelay < 15.200000 then 'rs7' 
        when SecurityDelay > 7.600000 and SecurityDelay <= 7.800000 then 'ls8' 
        when SecurityDelay >= 15.200000 and SecurityDelay < 15.600000 then 'rs8' 
        when SecurityDelay > 7.800000 and SecurityDelay <= 8.000000 then 'ls9' 
        when SecurityDelay >= 15.600000 and SecurityDelay < 16.000000 then 'rs9' 
        when SecurityDelay >= 8.000000 and SecurityDelay <= 12.000000 then 'c' 
        when SecurityDelay = 8.000000 then 'c1' 
        when SecurityDelay = 12.000000 then 'c2'
    end as range 
    from flights where SecurityDelay between 6.000000 and 16.000000) t group by t.range;

 range | nbocc 
-------+-------
       |   532
 rs5   |   168
 rs7   |   286
 c     |   749
 rs2   |   170
 rs0   |   211
 ls4   |   350
 ls9   |   286
 
SELECT *, pg_size_pretty(total_bytes) AS total
    , pg_size_pretty(index_bytes) AS INDEX
    , pg_size_pretty(toast_bytes) AS toast
    , pg_size_pretty(table_bytes) AS TABLE
  FROM (
  SELECT *, total_bytes-index_bytes-COALESCE(toast_bytes,0) AS table_bytes FROM (
      SELECT c.oid,nspname AS table_schema, relname AS TABLE_NAME
              , c.reltuples AS row_estimate
              , pg_total_relation_size(c.oid) AS total_bytes
              , pg_indexes_size(c.oid) AS index_bytes
              , pg_total_relation_size(reltoastrelid) AS toast_bytes
          FROM pg_class c
          LEFT JOIN pg_namespace n ON n.oid = c.relnamespace
          WHERE relkind = 'r' and relname = 'flights_150k'
  ) a
) a;

