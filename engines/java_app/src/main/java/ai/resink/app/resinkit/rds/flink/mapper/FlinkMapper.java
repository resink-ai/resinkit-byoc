package ai.resink.app.resinkit.rds.flink.mapper;


import org.apache.ibatis.annotations.Insert;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Select;
import org.apache.ibatis.annotations.Update;

import java.util.List;
import java.util.Map;

@Mapper
public interface FlinkMapper {

    @Update("CREATE TABLE T(a INT, b VARCHAR(10)) WITH ('connector' = 'filesystem', 'path' = 'file:///tmp/T.csv', 'format' = 'csv')")
    void createTable();

    @Insert("INSERT INTO T VALUES (1, 'Hi'), (2, 'Hello')")
    void insertData();

    @Select("SELECT * FROM T")
    List<Map<String, Object>> selectAllFromT();
}