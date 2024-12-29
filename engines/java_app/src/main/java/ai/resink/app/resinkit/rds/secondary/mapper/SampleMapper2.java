// (C)2024 resink.ai
package ai.resink.app.resinkit.rds.secondary.mapper;

import org.apache.ibatis.annotations.Select;

public interface SampleMapper2 {
    @Select("SELECT 'Hello World!'")
    String select2();
}
