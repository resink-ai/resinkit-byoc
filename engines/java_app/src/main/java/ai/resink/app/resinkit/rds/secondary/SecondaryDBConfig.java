// (C)2024 resink.ai
package ai.resink.app.resinkit.rds.secondary;

import com.zaxxer.hikari.HikariConfig;
import com.zaxxer.hikari.HikariDataSource;
import org.apache.ibatis.session.SqlSessionFactory;
import org.mybatis.spring.SqlSessionFactoryBean;
import org.mybatis.spring.SqlSessionTemplate;
import org.mybatis.spring.annotation.MapperScan;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import javax.sql.DataSource;

@Configuration
@MapperScan(value = "ai.resink.app.resinkit.rds.secondary.mapper", sqlSessionFactoryRef = "secondarySqlSessionFactory")
public class SecondaryDBConfig {

    // ref:
    // https://docs.spring.io/spring-boot/docs/2.0.x/reference/html/howto-data-access.html
    // https://mdwgti16.github.io/spring%20boot/spring_boot_mybatis_multi/#

    @Bean
    @Qualifier("secondaryHikariConfig")
    @ConfigurationProperties(prefix = "spring.datasource.secondary")
    public HikariConfig secondaryHikariConfig() {
        return new HikariConfig();
    }

    @Bean
    @Qualifier("secondaryDataSource")
    public DataSource secondaryDataSource() {
        return new HikariDataSource(secondaryHikariConfig());
    }

    @Bean(name = "secondarySqlSessionFactory")
    public SqlSessionFactory sqlSessionFactory(@Qualifier("secondaryDataSource") DataSource dataSource)
            throws Exception {
        SqlSessionFactoryBean sqlSessionFactoryBean = new SqlSessionFactoryBean();
        sqlSessionFactoryBean.setDataSource(dataSource);
        return sqlSessionFactoryBean.getObject();
    }

    @Bean(name = "secondarySqlSessionTemplate")
    public SqlSessionTemplate sqlSessionTemplate(
            @Qualifier("secondarySqlSessionFactory") SqlSessionFactory sqlSessionFactory) {
        return new SqlSessionTemplate(sqlSessionFactory);
    }
}
